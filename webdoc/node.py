from common import *
from collections import MutableMapping, MutableSequence

is_string = lambda x:isinstance(x,basestring)

__all__ = ['Node']
class Node(MutableMapping, MutableSequence):
	'''An object with a name, children and attributes, used to represent components
	of a document.
	
	>>> rep = lambda x:sorted(vars(x).items())
	>>> Node('x')
	Node('x')
	>>> Node('y', 1, 2, 3, a=5)
	Node('y', 1, 2, 3, _a=5)
	>>> n = Node('n', r='s')
	>>> n.append('o')
	>>> n.extend(['p', 'z'])
	>>> n[-1] = 'q'
	>>> n['r'] = 'r'
	>>> n
	Node('n', 'o', 'p', 'q', _r='r')
	>>> n.update(_s='t', r=0)
	>>> del n['r']
	>>> n.pop(1)
	'p'
	>>> n
	Node('n', 'o', 'q', _s='t')

	An underscore '_' is prepended to all attribute names to allow for attribute
	names that are also python keywords such as 'class', which is a valid concern e.g. in
	xml. To set set a literal attribute '_name', use two underscores: '__name'.
	repr() is unaffected so that eval(repr(Node(...))) evaluates to the original
	Node value.

	>>> a = Node('a', _class='123')
	>>> a
	Node('a', _class='123')
	>>> a['class'] = '234'
	>>> a
	Node('a', _class='234')
	>>> print a
	Node('a', class='234')
	
	If the first argument is another node, that node's values are copied. The 
	other arguments are ignored.
	
	>>> b = Node.copy(a)
	>>> b
	Node('a', _class='234')
	>>> b.children is a.children
	False
	>>> b.attributes is a.attributes
	False
	>>> is_sequence(Node())
	False
	
	Use Node.walk to iterate over its entire tree.
	
	>>> doc = Node('a', Node('b', 'c', Node('d', e='f')))
	>>> for depth, element in doc.walk():
	...   if isinstance(element, Node):
	...     print '  '*depth, element.name, element.attributes
	...   else:
	...     print '  '*depth, `element`
	 a {}
	   b {}
	     'c'
	     d {'_e': 'f'}
	'''
	__sequence__ = False
	def __init__(self, name=None, *children, **attributes):
		self.name = name
		self.children = list(children)
		self.attributes = dict((self._attr_key(k),v) for k,v in attributes.items())
	
	@classmethod
	def copy(cls, node):
		return cls(node.name, *node.children, **node.attributes)
	
	@staticmethod
	def _attr_key(key):
		return key if key[0]=='_' else '_'+key
	
	def __getitem__(self, key):
		if is_string(key):
			return self.__dict__['attributes'][self._attr_key(key)]
		else:
			return self.__dict__['children'][key]
	
	def __setitem__(self, key, value):
		if is_string(key):
			self.__dict__['attributes'][self._attr_key(key)] = value
		else:
			self.__dict__['children'][key] = value
	
	def __delitem__(self, key):
		if is_string(key):
			del self.attributes[self._attr_key(key)]
		else:
			del self.children[key]
	
	def __len__(self):
		return len(self.children)
		
	def insert(self, place, value):
		self.children.insert(place, value)
		
	def _real_attrs(self):
		return dict((k[1:],v) if k[0]=='_' else (k,v) for k,v in self.attributes.iteritems())
		
	def __repr__(self):
		return '%s(%s)'%(self.__class__.__name__,', '.join([repr(self.name)] + \
		  map(repr,self.children) + \
		  ['%s=%r'%i for i in self.attributes.items()]))
		
	def __str__(self):
		return '%s(%s)'%(self.__class__.__name__,', '.join([repr(self.name)] + \
		  map(repr,self.children) + \
		  ['%s=%r'%i for i in self._real_attrs().items()]))
		  
	def __nonzero__(self):
		return True
		
	def walk(self, filter=None, depth=0):
		yield depth, self
		for element in self.children:
			if isinstance(element, Node):
				for d,sub in element.walk(depth=depth+1):
					yield d,sub
			else:
				yield depth+1, element

__all__.append('NoChildrenMixin')
class NoChildrenMixin(object):
	'''Node mixin which ignores getting and setting children
	
	This mixin is useful for node types which are always leaf nodes, for example
	<br /> tags in html.'''
	children = property(lambda s:[], lambda s,v:None)

__all__.append('NoAttributesMixin')
class NoAttributesMixin(object):
	'''Node mixin which ignores getting and setting attributes.
	
	This mixin is useful for node types which never need attributes set, for
	example raw text nodes.'''
	attributes = property(lambda s:{}, lambda s,v:None)

__all__.append('NoNameMixin')
class NoNameMixin(Node):
	'''Node mixin which reroutes name access to children.
	
	This mixin is useful for node types, for which it doesn't make sense to
	have a name, for example comment nodes.'''
	def __init__(self, *children, **attributes):
		Node.__init__(self, None, *children, **attributes)
	#@property
	#def children(self):
		#return self._children
	#@children.setter
	#def children(self, value):
		#self._children = [None] + list(value)
		
	#@property
	#def name(self):
		#return None
	#@name.setter
	#def name(self, value):
		## Node.__init__ always sets children before name, so this shouldn't cause problems
		#self._children[0] = value

if __name__=='__main__':
	import doctest
	doctest.testmod()
