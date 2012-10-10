#!/usr/bin/env python

from urlparse import parse_qsl

from .. import MultiDict

class Query(MultiDict):
	"""

	>>> q = Query.parse('a=1&b=2&a=3')
	>>> sorted(q.items())
	[('a', '1'), ('a', '3'), ('b', '2')]
	"""
	keep_blank_values = True
	strict_parsing = False
	@classmethod
	def parse(cls, line):
		return cls(parse_qsl(line, cls.keep_blank_values, cls.strict_parsing))
