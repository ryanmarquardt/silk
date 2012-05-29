
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

if __name__=='__main__':
	import doctest
	doctest.testmod()
