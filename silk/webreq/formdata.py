#!/usr/bin/env python

# Derived from python standard library cgi.py

import sys
import os
from urlparse import parse_qsl

from silk import container, MultiDict
import silk.webreq.header
from silk.webreq.header import Header, HeaderList
from silk.webreq.uri import URI
from silk.webreq.query import Query

__all__ = ["FormData"]

def watch(iterable, *sentinels):
	for value in iterable:
		if value in sentinels:
			break
		yield value

def delimited(iterable, delim, *sentinels, **kwargs):
	block_size = max(1024, kwargs.get('block_size', 8192))
	remainder = ''
	size = -len(delim)
	for value in iter(lambda:iterable.readline(block_size), None):
		if value in sentinels:
			break
		if value.endswith(delim):
			value, remainder = remainder + value[:size], delim
		else:
			value, remainder = remainder + value, ''
		yield value

class FormData(MultiDict):
	@classmethod
	def parse_raw(cls, infile):
		return cls.parse(infile, dict(Header.parse(line) for line in iter(infile.next, '\r\n'))['Content-Type'])

	def handle_upload(self, name, iterable, filename, content_type):
		class FakeFile(str):
			def __new__(cls, filename, mimetype, value):
				self = str.__new__(cls, value)
				self.filename, self.mimetype = filename, mimetype
				return self
			def __repr__(self):
				return 'Upload(%r, %r, %s)' % (self.filename, self.mimetype, str.__repr__(self))
		return FakeFile(filename, content_type, ''.join(iterable))

	def handle_value(self, name, iterable):
		return ''.join(iterable)

	@classmethod
	def parse(cls, infile, content_type_header):
		"""

		Typically, called like:
		#>>> v = FormData.parse(sys.stdin, env['CONTENT_TYPE'])
		"""
		self = cls()
		def parse_multipart(infile, post_head, outerboundaries=()):
			boundary = post_head['Content-Type']['boundary']
			sep, term = '--%s\r\n' % boundary, '--%s--\r\n' % boundary
			infile.readline() #Ignore initial boundary
			while True:
				headers = dict(Header.parse(line) for line in watch(infile, '', '\r\n', *outerboundaries))
				if not headers:
					break
				cd = headers['Content-Disposition']
				name = cd.get('name') or post_head['Content-Disposition']['name']
				if 'Content-Type' in headers:
					ct = headers['Content-Type']
					if ct.key.startswith('multipart/'):
						for name, content in parse_multipart(infile, headers, (sep, term)):
							yield name, content
					else:
						#File upload
						yield name, self.handle_upload(name,
							delimited(infile, '\r\n', '', sep, term, *outerboundaries),
							cd.get('filename',''), ct.key)
				else:
					#Text value
					yield name, self.handle_value(name, delimited(infile, '\r\n', '', sep, term, *outerboundaries))
		ct = content_type_header if isinstance(content_type_header, silk.webreq.header.Header) else Header.parse_value(content_type_header)
		if ct.key == 'multipart/form-data':
			self.update(parse_multipart(infile, {'Content-Type':ct}))
		elif ct.key == 'application/x-www-form-urlencoded':
			self.update(Query.parse(infile.readline(8192).strip()))
		return self

if __name__=='__main__':
	import doctest
	doctest.testmod()
