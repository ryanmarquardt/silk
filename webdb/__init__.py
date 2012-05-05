"""


Use the connect method to open a database connection.
>>> mydb = DB.connect('sqlite','/tmp/webdb.doctest.sqlite')
>>> import os
>>> os.unlink('/tmp/webdb.doctest.sqlite')

By default, an in-memory database is created.
>>> mydb = DB()

Currently only sqlite databases are supported. Other databases will be supported
with drivers. See webdb.drivers documentation for more information.


Tables are defined by assigning them to attributes of a database. Two special
methods help with definitions.

Conform reads table definitions from the database, overriding any tables
that have already been defined.
>>> mydb.conform()
>>> list(mydb) #No table definitions
[]

>>> mydb.test_table = Table(Column('key'), Column('value'))
>>> list(mydb)
[Table(Column('key', 'string'), Column('value', 'string'))]

>>> mydb.test_table = Table(Column('key'), Column('value'), Column('extra'))
>>> list(mydb)
[Table(Column('extra', 'string'), Column('key', 'string'), Column('value', 'string'))]

>>> mydb.conform()
>>> list(mydb)
[Table(Column('key', 'string'), Column('value', 'string'))]

Migrate modifies tables in the database to be like newly-assigned tables.
>>> mydb.test_table = Table(Column('key'), Column('value'), Column('extra'))
>>> mydb.migrate()
>>> mydb.test_table
Table(Column('extra', 'string'), Column('key', 'string'), Column('value', 'string'))

Conforming after a migration does nothing.
>>> mydb.conform()
>>> mydb.test_table
Table(Column('extra', 'string'), Column('key', 'string'), Column('value', 'string'))

Add some data by calling insert on a table. An integer referring to the new row
is returned and can be used to retrieve it later.
>>> i = mydb.test_table.insert(key='1', value='a')
>>> row = mydb.test_table[i]
>>> row.key
'1'
>>> row.value
'a'
>>> print row.extra
None

"""
import collections
import inspect
import drivers.sqlite

from webdoc.common import container

class collection(collections.MutableSet):
	'''Set of objects which can also be retrieved by name

	>>> class b(object):
	...   def __init__(self, name, value):
	...     self.name, self.value = name, value
	...   def __repr__(self): return 'b(%r, %r)' % (self.name, self.value)
	>>> a = collection()
	>>> a.add(b('robert', 'Sys Admin'))
	>>> a.add(b('josephine', 'Q/A'))
	>>> a['robert']
	b('robert', 'Sys Admin')
	>>> sorted(list(a), key=lambda x:x.name)
	[b('josephine', 'Q/A'), b('robert', 'Sys Admin')]
	'''
	def __init__(self, elements=(), namekey='name'):
		self._key = namekey
		self._data = dict((getattr(e,namekey),e) for e in elements)

	def __len__(self):
		return len(self._data)

	def __iter__(self):
		return self._data.itervalues()

	def __contains__(self, value):
		return getattr(value,self._key) in self._data

	def add(self, value):
		self._data[getattr(value,self._key)] = value

	def discard(self, value):
		del self._data[getattr(value,self._key)]

	def keys(self):
		return self._data.keys()

	def __getitem__(self, key):
		return self._data[key]

	def __delitem__(self, key):
		del self._data[key]

	def pop(self, *item):
		assert len(item) <= 1
		if item:
			return self._data.pop(item[0])
		else:
			return self._data.popitem()[1]

class Row(object):
	pass

class Selection(object):
	pass
	
class Set(object):
	pass

ident = lambda x:x

class Column(object):
	'''Column(name, type='string', notnull=False, default=None)
	
	valid types:
	'string' or basestring
	'text'
	'integer' or int
	'boolean' or bool
	'''
	def __init__(self, name, type='string', notnull=False, default=None):
		self.name = name
		if type == 'string':
			self.type = 'string'
			self.interpret = str
			self.represent = str
		else:
			self.type = type
			self.interpret = ident
			self.represent = ident
		self.notnull = notnull
		self.default = default
		self.index = None
		
	def __repr__(self):
		values = [`self.name`]
		values.append(`self.type`)
		if self.notnull:
			values.append('notnull=True')
		if not self.default is None:
			values.append('default=%r' % self.default)
		return 'Column(%s)' % ', '.join(values)
		
	def __cmp__(self, x):
		return cmp((self.name,vars(self)), (x.name,vars(self))) if x else 1

class Table(collection):
	def __init__(self, *columns, **kwargs):
		collection.__init__(self, columns)

	def __getattr__(self, key):
		return collection.__getitem__(self, key)

	def __delattr__(self, key):
		collection.__delitem__(self, key)

	def __getitem__(self, key):
		names = self.keys()
		columns = list(self)
		values = self._db.__driver__.select(names, self._name, [('rowid',key)])[0]
		return container((k,c.represent(v)) for k,v,c in zip(['rowid']+names,values,columns))

	def __delitem__(self, key):
		pass

	def insert(self, **values):
		return self._db.__driver__.insert(values, self._name)

	def __repr__(self):
		return 'Table(%s)' % ', '.join(sorted(map(repr,self)))

class DB(collection):
	"""
	
	>>> mydb = DB.connect('sqlite')
	>>> mydb.test = Table(Column('data'))
	>>> list(mydb)
	[Table(Column('data', 'string'))]
	"""
	__driver__ = drivers.sqlite.sqlite()

	def __init__(self):
		collection.__init__(self, namekey='_name')
	
	def __setitem__(self, key, value):
		assert isinstance(value, Table)
		value._db = self
		value._name = key
		self.__driver__.create_table_if_nexists(key, value)
		collection.add(self, value)

	def __setattr__(self, key, value):
		if key[0] == '_':
			super(DB, self).__setattr__(key, value)
		else:
			self[key] = value

	def __getattr__(self, key):
		if key[0] == '_':
			return super(DB, self).__getattr__(key)
		else:
			return self[key]
	
	def __delattr__(self, key):
		if key[0] == '_':
			super(DB, self).__delattr__(key)
		else:
			del self[key]

	@classmethod
	def connect(cls, name, *args, **kwargs):
		driver = getattr(__import__('drivers.%s'%name, fromlist=name), name)
		newcls = type(cls.__name__, (cls,), {'__driver__':driver(*args,**kwargs)})
		return newcls()
		
	def conform(self):
		for table in self.__driver__.list_tables():
			columns = []
			for name,v_type,notnull,default in self.__driver__.list_columns(table):
				columns.append(Column(name, v_type, notnull=notnull, default=default))
			t = Table(*columns)
			t._db = self
			t._name = table
			collection.add(self, t)
		
	def migrate(self):
		names = set(self.keys())
		db_tables = set(self.__driver__.list_tables())
		for name in names - db_tables:
			#Create
			self.__driver__.create_table(name, self[name])
		for name in names.intersection(db_tables):
			#Alter if not the same
			self.__driver__.alter_table(name, self[name])

if __name__=='__main__':
	import doctest
	doctest.testmod()
