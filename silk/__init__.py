
import collections

class container(dict):
	'''dict whose items can be retrieved as attributes
	
	>>> c = container(a=1, b=2)
	>>> c.a
	1
	>>> c.b
	2
	>>> c.a = 3
	>>> c['a']
	3
	
	If a key isn't found, None is returned...
	
	>>> print c.c
	None
	
	but item access raises an exception
	>>> c['c']
	Traceback (most recent call last):
	  ...
	KeyError: 'c'
	'''
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__
	__delattr__ = dict.__delitem__

def sequence(x):
	'''Converts its argument into a list, but is sensitive to arguments that are \
	iterable but not iterators (i.e. strings)
	
	>>> sequence(0)
	[0]
	>>> sequence('0')
	['0']
	>>> sequence(u'123')
	[u'123']
	>>> sequence((1,2,3))
	[1, 2, 3]
	>>> sequence(a*2+1 for a in range(5))
	[1, 3, 5, 7, 9]
	>>> sequence([])
	[]
	'''
	return list(x) if is_sequence(x) else [x]

def is_sequence(x):
	'''Determines whether its argument is a proper sequence (i.e. list, tuple,
	but not string)
	
	>>> is_sequence(None)
	False
	>>> is_sequence('None')
	False
	>>> is_sequence(u'None')
	False
	>>> is_sequence(['None'])
	True
	>>> is_sequence({'a':'b'})
	True
	>>> is_sequence((None,))
	True
	
	Setting the class attribute __sequence__ to a false value can override any
	other criteria
	
	>>> class A(list):
	...   pass
	>>> class B(list):
	...   __sequence__ = False
	>>> is_sequence(A())
	True
	>>> is_sequence(B())
	False
	'''
	#Takes advantage of the fact that strings don't have an __iter__ method,
	# but doesn't limit inputs to subclasses of standard types, and doesn't
	# match positive with string types. (this might need to change to remain portable)
	return hasattr(x,'__iter__') and getattr(x,'__sequence__',True)

def flatten(x):
	'''Converts nested iterators into a single list. As with sequence(x), strings
	are not considered to be iterators.
	
	>>> flatten(1)
	[1]
	>>> flatten('123')
	['123']
	>>> flatten([1, [2], [[3]]])
	[1, 2, 3]
	>>> flatten([1, [2, [3, [[4]]]]])
	[1, 2, 3, 4]
	'''
	return [a for i in x for a in flatten(i)] if is_sequence(x) else [x]

class collection(collections.MutableSet, collections.MutableMapping):
	'''Set of objects which can also be retrieved by name

	>>> class b(object):
	...   def __init__(self, name, value):
	...     self.name, self.value = name, value
	...   def __repr__(self): return 'b(%r, %r)' % (self.name, self.value)
	>>> a = collection('name')
	>>> a.add(b('robert', 'Sys Admin'))
	>>> a.add(b('josephine', 'Q/A'))
	>>> a['robert']
	b('robert', 'Sys Admin')
	>>> sorted(list(a), key=lambda x:x.name)
	[b('josephine', 'Q/A'), b('robert', 'Sys Admin')]
	>>> a['stephanie'] = b('robert', 'Sys Admin')
	>>> a['stephanie']
	b('stephanie', 'Sys Admin')
	>>> len(a)
	3
	>>> del a['robert']
	>>> a.pop('josephine', 'Q/A')
	Traceback (most recent call last):
		...
	TypeError: collection.pop takes at most 1 argument (got 2)
	>>> a.pop('josephine')
	b('josephine', 'Q/A')
	>>> a.pop()
	b('stephanie', 'Sys Admin')
	'''
	def __init__(self, namekey, elements=()):
		self._key = namekey
		self._data = dict((getattr(e,namekey),e) for e in elements)

	def __len__(self):
		return len(self._data)

	def __iter__(self):
		return self._data.itervalues()

	def __contains__(self, value):
		return value in self._data or getattr(value,self._key) in self._data.values()

	def add(self, value):
		self._data[getattr(value,self._key)] = value

	def discard(self, value):
		del self._data[getattr(value,self._key)]

	def keys(self):
		return self._data.keys()

	def __getitem__(self, key):
		return self._data[key]
		
	def __setitem__(self, key, value):
		setattr(value, self._key, key)
		self._data[key] = value

	def __delitem__(self, key):
		del self._data[key]

	def pop(self, *item):
		if len(item) > 1:
			raise TypeError('collection.pop takes at most 1 argument (got %i)' % len(item))
		if item:
			return self._data.pop(item[0])
		else:
			return self._data.popitem()[1]

class ordered_collection(collection):
	def __init__(self, namekey, elements=()):
		self._key = namekey
		self._data = collections.OrderedDict((getattr(e,namekey),e) for e in elements)


class MultiDict(collections.MutableMapping):
	"""

	>>> MultiDict()
	MultiDict({})
	>>> m = MultiDict([('a', 1), ('b', 2), ('a', 3)])
	>>> m['a']
	[1, 3]
	>>> m['b']
	[2]
	>>> m.a
	3
	>>> m.b
	2
	>>> 'c' in m
	False
	>>> print m.c
	None
	"""
	def __init__(self, init=(), **kwargs):
		if isinstance(init, MultiDict):
			self._dict = init._dict.__copy__()
		else:
			self._dict = collections.defaultdict(list)
			self.update(init or kwargs)

	def update(self, other):
		for key, value in getattr(other, 'iteritems', other.__iter__)():
			self[key] = value

	def __contains__(self, key):
		return key in self._dict

	def __getitem__(self, key):
		return self._dict[key]

	def __setitem__(self, key, value):
		self._dict[key].append(value)

	def __delitem__(self, key):
		del self._dict[key]

	def __len__(self):
		return len(self._dict)

	def __iter__(self):
		return iter(self._dict)

	def pop(self, key, index=-1):
		r = self._dict[key].pop(index)
		if not self._dict[key]:
			del self._dict[key]
		return r

	def get(self, key, default=None):
		try:
			return self._dict[key][-1]
		except (IndexError, KeyError):
			return default
	__getattr__ = get

	def __delattr__(self, key):
		self._dict.pop(key)

	def iteritems(self):
		for key in self._dict:
			for value in self._dict[key]:
				yield key, value

	def items(self):
		return list(self.iteritems())

	getlist = __getitem__

	def __repr__(self):
		return '%s(%s)' % (self.__class__.__name__,dict.__repr__(self._dict))

__all__ = ['container', 'sequence', 'is_sequence', 'flatten', 'collection', 'ordered_collection', 'MultiDict']
