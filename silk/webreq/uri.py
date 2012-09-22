#!/usr/bin/env python

from urlparse import urlsplit, urlunsplit
from urllib import urlencode
from wsgiref.util import request_uri

from silk import MultiDict
from silk.webreq.query import Query

class URI(object):
	def __init__(self, uri='', scheme='', host='', path=None, query=None, anchor=''):
		self.scheme, self.host, self.path, self.query, self.anchor = urlsplit(uri, scheme='http')
		self.scheme = scheme or self.scheme
		self.host = host or self.host
		self.path = path or self.path or '/'
		self.query = query or self.query or Query()
		self.anchor = anchor or self.anchor

	@property
	def path(self):
		return self.__dict__['path']
	@path.setter
	def path(self, new):
		new = new or '/'
		if isinstance(new, basestring):
			new = new[1:].split('/')
		self.__dict__['path'] = new

	@property
	def query(self):
		return self.__dict__['query']
	@query.setter
	def query(self, new):
		if isinstance(new, basestring):
			new = Query.parse(new)
		elif not isinstance(new, Query):
			new = Query(new)
		self.__dict__['query'] = new

	def get_path(self):
		return '/'.join(['']+self.path)

	def get_query(self):
		return urlencode(self.query)

	@classmethod
	def from_env(cls, env):
		return cls(request_uri(env))

	def __str__(self):
		return urlunsplit((self.scheme, self.host, self.get_path(), self.get_query(), self.anchor))

	def __repr__(self):
		return 'URI(%r)' % (str(self),)
