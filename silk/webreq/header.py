#!/usr/bin/env python

from email.utils import quote as param_quote, unquote as param_unquote

class Header(dict):
	def __init__(self, key, *args, **kwargs):
		dict.__init__(self, *args, **kwargs)
		self.key = key

	@classmethod
	def parse(cls, line):
		name, _, value = line.partition(': ')
		return name.replace('-',' ').title().replace(' ','-'), cls.parse_value(value)

	@classmethod
	def parse_value(cls, line):
		def _parseparam(s):
			while s[:1] == ';':
				s = s[1:]
				end = s.find(';')
				while end > 0 and s.count('"', 0, end) % 2:
					end = s.find(';', end + 1)
				if end < 0:
					end = len(s)
				f = s[:end]
				yield f.strip()
				s = s[end:]
		parts = _parseparam(';' + line)
		self = cls(next(parts))
		for p in parts:
			i = p.find('=')
			if i >= 0:
				self[p[:i].strip().lower()] = param_unquote(p[i+1:].strip())
		return self

	def __str__(self):
		return '; '.join([self.key] + [i[0] if i[1] is None else ('%s=%s' % i) for i in list(self.items())])

	def __repr__(self):
		return 'Header(%s)' % ', '.join([repr(self.key)] + [repr(i[0]) if i[1] is None else ('%s=%r' % i) for i in list(self.items())])

class HeaderList(list):
	def append(self, name, key, **props):
		if isinstance(key, Header):
			list.append(self, (name, key))
		else:
			list.append(self, (name, Header(key, **props)))

	def __setitem__(self, name, value):
		try:
			idx = zip(*self)[0].index(name)
		except (ValueError, IndexError):
			self.append(name, value)
		else:
			if isinstance(value, Header):
				list.__setitem__(self, idx, (name, value))
			else:
				list.__setitem__(self, idx, (name, Header(value)))

	def __getitem__(self, name):
		try:
			idx = zip(*self)[0].index(name)
		except (ValueError, IndexError):
			raise KeyError
		return list.__getitem__(self, idx)[1]

	def as_list(self):
		return [(name, str(header)) for name, header in self]
