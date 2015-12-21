#!/usr/bin/env python

# Derived from python standard library cgi.py

import sys
import os
from urllib.parse import parse_qsl

from .. import container, MultiDict
from . import header
from .header import Header, HeaderList
from .uri import URI
from .query import Query

__all__ = ["FormData"]

def watch(iterable, *sentinels):
	for value in iterable:
		if value in sentinels:
			break
		yield value

def delimited(iterable, delim, *sentinels):
	remainder = ''
	size = -len(delim)
	for value in iterable:
		if value in sentinels:
			break
		if value.endswith(delim):
			value, remainder = remainder + value[:size], delim
		else:
			value, remainder = remainder + value, ''
		yield value

def read_bounded(filelike, size, buffer_size=8192):
	remaining = size
	while remaining > 0:
		buffer = filelike.read(min(buffer_size, remaining))
		remaining -= len(buffer)
		yield buffer

def iter_lines(iterable, delim='\r\n'):
	buffer = ''
	for chunk in iterable:
		buffer += chunk
		while True:
			line,d,buffer = buffer.partition(delim)
			if d:
				yield line+d
			else:
				buffer = line
				break
	while True:
		line,d,buffer = buffer.partition(delim)
		if line or d:
			yield line+d
		else:
			return

class FormData(MultiDict):
	@classmethod
	def parse_raw(cls, infile):
		return cls.parse(infile, dict(Header.parse(line) for line in iter(infile.__next__, '\r\n'))['Content-Type'])

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
	def parse(cls, infile, content_type_header, content_length, *extra_args, **extra_kwargs):
		"""

		Typically, called like:
		#>>> v = FormData.parse(sys.stdin, env['CONTENT_TYPE'])
		"""
		self = cls()
		def parse_multipart(iterin, post_head, outerboundaries=()):
			boundary = post_head['Content-Type']['boundary']
			sep, term = '--%s\r\n' % boundary, '--%s--\r\n' % boundary
			next(iterin) #Ignore initial boundary
			while True:
				headers = dict(Header.parse(line) for line in watch(iterin, '', '\r\n', *outerboundaries))
				if not headers:
					break
				cd = headers['Content-Disposition']
				name = cd.get('name') or post_head['Content-Disposition']['name']
				if 'Content-Type' in headers:
					ct = headers['Content-Type']
					if ct.key.startswith('multipart/'):
						for name, content in parse_multipart(iterin, headers, (sep, term)):
							yield name, content
					else:
						#File upload
						yield name, self.handle_upload(name,
							delimited(iterin, '\r\n', '', sep, term, *outerboundaries),
							cd.get('filename',''), ct.key, *extra_args, **extra_kwargs)
				else:
					#Text value
					yield name, self.handle_value(name, delimited(iterin, '\r\n', '', sep, term, *outerboundaries), *extra_args, **extra_kwargs)
		iterin = iter_lines(read_bounded(infile, content_length))
		if content_type_header.key == 'multipart/form-data':
			self.update(parse_multipart(iterin, {'Content-Type':content_type_header}))
		elif content_type_header.key == 'application/x-www-form-urlencoded':
			self.update(Query.parse(iterin.next().strip()))
		return self
