"""Database abstraction layer

Use the connect method to open a database connection.
>>> mydb = DB.connect('sqlite','path/to/database.sqlite')
Traceback (most recent call last):
 ...
IOError: [Errno 2] No such file or directory: 'path/to/database.sqlite'

By default, an in-memory database is created.
>>> mydb = DB()

Currently only sqlite databases are supported. Other databases will be supported
with drivers. See webdb.drivers documentation for more information.

===
Tables
===

Tables are defined by assigning them to attributes of a database. Two special
methods help with definitions.

Conform reads table definitions from the database, overriding any tables
that have already been defined.
>>> mydb.conform()
>>> list(mydb) #No tables defined yet
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
>>> mydb.test_table = Table(Column('key', 'integer'), Column('value'), Column('extra'))
>>> mydb.migrate()
>>> mydb.test_table
Table(Column('extra', 'string'), Column('key', 'integer'), Column('value', 'string'))

Conforming after a migration keeps the same columns, but other information might
be lost. For example column data types might be lost (sqlite migrations don't
change data types, boolean columns might be interpretted as integers, etc.)
>>> mydb.conform()
>>> mydb.test_table
Table(Column('extra', 'string'), Column('key', 'string'), Column('value', 'string'))

It is always recommended to conform your database *before* defining columns.
>>> mydb.test_table = Table(Column('key', 'integer'), Column('value'), Column('extra'))

Conforming and migrating are both optional. Attempting to manipulate the
database without these calls may fail if table definitions don't match tables
in the database. However, conform unconditionally reads all tables, so it may
not be appropriate for large databases. Be careful using migrate on databases
that are shared between applications, as it can break those applications if
a table is renamed or altered.

===
Data
===

Add some data by calling insert on a table. An integer referring to the new row
is returned and can be used to retrieve it later.
>>> mydb = DB()
>>> mydb.test_table = Table(Column('key', 'integer'), Column('value'))

Insert adds a row to the table and returns its row id
>>> mydb.test_table.insert(key='100', value='a')
1
>>> row = mydb.test_table[1]
>>> row.key
100
>>> row.value
'a'
>>> del mydb.test_table[1]

===
Consistency
===

The database acts as a context manager which controls data integrity. If several
operations need to be treated atomically:

If an error is raised, the all of the transactions are rolled back. Only the
outer-most context manager commits the transaction. Individual calls that modify
the database are wrapped in their own context managers, so they are committed
automatically.
>>> with mydb:
...   mydb.test_table.insert(key=3, value='c')
...   mydb.test_table.insert(key=4, value='d')
...   raise Exception
Traceback (most recent call last):
 ...
Exception
>>> list(mydb.test_table.select())
[]

>>> with mydb:
...   mydb.test_table.insert(key=3, value='c')
...   mydb.test_table.insert(key=7, value='g')
1
2
>>> for row in mydb.test_table.select():
...   print sorted(row.items())
[('key', 3), ('rowid', 1), ('value', 'c')]
[('key', 7), ('rowid', 2), ('value', 'g')]

===
Querying
===

Doing comparison, binary or arithmetic operations on columns produces 'Where'
objects.
>>> mydb.test_table.key <= 3
Where([LESSEQUAL, Column('key', 'integer'), 3])

The resulting object can be queried. Standard SQL commands are provided. Using
parentheses, a query can be set up and then selected:
>>> for row in (mydb.test_table.key<=3).select():
...   print sorted(row.items())
[('key', 3), ('rowid', 1), ('value', 'c')]

Rows in a query can be counted...
>>> (mydb.test_table.key>1).count()
2

or updated...
>>> (mydb.test_table.value=='c').update(key=4)
>>> for row in mydb.test_table.select():
...   print sorted(row.items())
[('key', 4), ('rowid', 1), ('value', 'c')]
[('key', 7), ('rowid', 2), ('value', 'g')]

or deleted...
>>> (mydb.test_table.key > 5).delete()
>>> for row in mydb.test_table.select():
...   print sorted(row.items())
[('key', 4), ('rowid', 1), ('value', 'c')]


"""
import collections
import inspect
import drivers.sqlite
try:
	import drivers.base
except ImportError:
	drivers.base = drivers.sqlite

from webdoc.common import container, flatten

class collection(collections.MutableSet, collections.MutableMapping):
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
	>>> a['stephanie'] = b('robert', 'Sys Admin')
	>>> a['stephanie']
	b('stephanie', 'Sys Admin')
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
		
	def __setitem__(self, key, value):
		setattr(value, self._key, key)
		self._data[key] = value

	def __delitem__(self, key):
		del self._data[key]

	def pop(self, *item):
		assert len(item) <= 1
		if item:
			return self._data.pop(item[0])
		else:
			return self._data.popitem()[1]

class Selection(object):
	def __init__(self, columns, values):
		self.columns = columns
		self.values = values
		
	def __iter__(self):
		for value in self.values:
			yield Row(self.columns, value)

class Row(container):
	def __init__(self, columns, values):
		container.__init__(self, [(c.name,c.represent(v)) for v,c in zip(values,columns)])

class Expression(object):
	def __eq__(self, x):
		return Where(self._db, [drivers.base.EQUAL, getattr(self,'_where_tree',self), x])
	def __ne__(self, x):
		return Where(self._db, [drivers.base.NOTEQUAL, getattr(self,'_where_tree',self), x])
	def __le__(self, x):
		return Where(self._db, [drivers.base.LESSEQUAL, getattr(self,'_where_tree',self), x])
	def __ge__(self, x):
		return Where(self._db, [drivers.base.GREATEREQUAL, getattr(self,'_where_tree',self), x])
	def __lt__(self, x):
		return Where(self._db, [drivers.base.LESSTHAN, getattr(self,'_where_tree',self), x])
	def __gt__(self, x):
		return Where(self._db, [drivers.base.GREATERTHAN, getattr(self,'_where_tree',self), x])
	
	def __add__(self, x):
		if isinstance(x, basestring) or \
		self.type in ('string','text','data') or \
		(isinstance(x, Column) and x.type in ('string','text','data')):
			return Where(self._db, [drivers.base.CONCATENATE, getattr(self,'_where_tree',self), x])
		else:
			return Where(self._db, [drivers.base.ADD, getattr(self,'_where_tree',self), x])
	def __sub__(self, x):
		return Where(self._db, [drivers.base.SUBTRACT, getattr(self,'_where_tree',self), x])
	def __mul__(self, x):
		return Where(self._db, [drivers.base.MULTIPLY, getattr(self,'_where_tree',self), x])
	def __div__(self, x):
		return Where(self._db, [drivers.base.DIVIDE, getattr(self,'_where_tree',self), x])
	def __floordiv__(self, x):
		return Where(self._db, [drivers.base.FLOORDIVIDE, getattr(self,'_where_tree',self), x])
	def __div__(self, x):
		return Where(self._db, [drivers.base.DIVIDE, getattr(self,'_where_tree',self), x])
	def __truediv__(self, x):
		return Where(self._db, [drivers.base.DIVIDE, getattr(self,'_where_tree',self), x])
	def __mod__(self, x):
		return Where(self._db, [drivers.base.MODULO, getattr(self,'_where_tree',self), x])

class Where(Expression):
	def __init__(self, db, where_tree):
		self._db = db
		self._where_tree = where_tree

	def _get_columns(self, columns):
		if not columns:
			columns = [table.ALL for table in self._get_tables()]
		return flatten(columns)
		
	def _get_tables(self):
		tables = set()
		for entity in flatten(self._where_tree):
			if isinstance(entity, Column):
				tables.add(entity.table)
		return tables
		
	def select(self, *columns):
		columns = self._get_columns(columns)
		values = self._db.__driver__.select(columns, self._where_tree)
		return Selection(columns, values)
		
	def select_one(self, *columns):
		columns = self._get_columns(columns)
		values = self._db.__driver__.select(columns, self._where_tree)
		return Row(columns, values.fetchone())
		
	def count(self):
		columns = [table.rowid for table in self._get_tables()]
		values = self._db.__driver__.select(columns, self._where_tree)
		return len(values.fetchall())
		
	def update(self, **values):
		self._db.__driver__.update(self._get_tables().pop()._name, self._where_tree, values)
		
	def delete(self):
		self._db.__driver__.delete(self._get_tables().pop()._name, self._where_tree)
		
	def __repr__(self):
		return 'Where(%r)'%self._where_tree

ident = lambda x:x

class Column(Expression):
	'''Column(name, type='string', notnull=False, default=None)
	
	valid types:
	'rowid'
	'string' or basestring
	'text'
	'integer' or int
	'float' or float
	'boolean' or bool
	'data' or bytes
	'''
	def __init__(self, name, datatype='string', notnull=False, default=None):
		self.name = name
		if isinstance(datatype, type):
			self.interpret = self.represent = datatype
			sample = datatype()
			if isinstance(sample, basestring):
				self.type = 'string'
			elif isinstance(sample, bool):
				self.type = 'boolean'
			elif isinstance(sample, int):
				self.type = 'integer'
			elif isinstance(sample, float):
				self.type = 'float'
			else:
				self.type = 'data'
		else:
			self.type = datatype
			if datatype in ('string','text','data'):
				self.interpret = self.represent = str
			elif datatype in ('integer','rowid'):
				self.interpret = self.represent = int
			elif type == 'float':
				self.interpret = self.represent = float
			elif type == 'boolean':
				self.interpret = self.represent = bool
			
		self.notnull = notnull
		self.default = default
		
	def __repr__(self):
		values = [`self.name`]
		values.append(`self.type`)
		if self.notnull:
			values.append('notnull=True')
		if not self.default is None:
			values.append('default=%r' % self.default)
		return 'Column(%s)' % ', '.join(values)
		
	@property
	def _db(self):
		return self.table._db
	
class Table(collection):
	def __init__(self, *columns, **kwargs):
		collection.__init__(self, columns)
		for c in columns:
			c.table = self

	@property
	def rowid(self):
		c = Column('rowid', 'rowid')
		c.table = self
		return c
		
	@property
	def ALL(self):
		return [self.rowid]+list(self)

	def __getattr__(self, key):
		return collection.__getitem__(self, key)

	def __delattr__(self, key):
		collection.__delitem__(self, key)
		
	def __hash__(self):
		return hash(self._name)

	def __getitem__(self, key):
		try:
			key = int(key)
		except ValueError:
			raise TypeError("rowid's must be integers")
		columns = self.ALL
		value = (self.rowid==key).select_one(columns)
		if not value:
			raise KeyError("No row with rowid %i" % key)
		return value

	def __delitem__(self, key):
		(self.rowid==key).delete()

	def insert(self, **values):
		return self._db.__driver__.insert(values, self._name)

	def select(self, *columns):
		return Where(self._db, None).select(*(columns or self.ALL))

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
		
	def __enter__(self):
		self.__driver__.__enter__()
		
	def __exit__(self, obj, exc, tb):
		self.__driver__.__exit__(obj, exc, tb)
	
	def __setitem__(self, key, value):
		assert isinstance(value, Table)
		value._db = self
		self.__driver__.create_table_if_nexists(key, value)
		collection.__setitem__(self, key, value)

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

	def where(self, *conditions):
		return reduce(lambda x,y:x&y, conditions)

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
