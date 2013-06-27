"""Database abstraction layer

webdb is a database abstraction layer inspired by web2py's DAL. The goal
of webdb is to be more succinct and offer better cross-table integration.


Use the connect method to open a database connection.
>>> mydb = DB.connect('sqlite','path/to/database.sqlite')
Traceback (most recent call last):
 ...
IOError: [Errno 2] No such file or directory: 'path/to/database.sqlite'

By default, an in-memory database is created.
>>> mydb = DB()

Currently only sqlite and mysql databases are supported. Other databases
may be supported with drivers. See webdb.drivers documentation for more
information.

===
Tables
===

Tables are created using the ``define_table`` method of any database
object. Two special methods help with table definitions: ``conform`` and
``migrate``.

``conform`` reads table definitions from the database, overriding any
tables that have already been defined.

>>> mydb.conform()

>>> list(mydb) #No tables defined yet
[]

>>> mydb.define_table('test_table', StrColumn('key'), StrColumn('value'))
>>> list(mydb)
[<Table 'test_table'>]

>>> mydb.define_table('test_table', StrColumn('key'), StrColumn('value'), StrColumn('extra'))
>>> list(mydb)
[<Table 'test_table'>]

>>> mydb.conform()
>>> list(mydb)
[<Table 'test_table'>]

Migrate modifies tables in the database to be like newly-assigned tables.
>>> mydb.define_table('test_table', IntColumn('key'), StrColumn('value'), StrColumn('extra'))
>>> #mydb.migrate()
>>> mydb.test_table
<Table 'test_table'>

Conforming after a migration keeps the same columns, but other information might
be lost. For example column data types might be lost (sqlite migrations don't
change data types, boolean columns might be interpretted as integers, etc.)
>>> mydb.conform()
>>> mydb.test_table
<Table 'test_table'>

It is always recommended to conform your database *before* defining columns.
>>> mydb.define_table('test_table', IntColumn('key'), StrColumn('value'), StrColumn('extra'))

>>> mydb.define_table('test_types',
... 	IntColumn('a'),
... 	BoolColumn('b'),
... 	StrColumn('c'),
... 	DateTimeColumn('e'),
... 	FloatColumn('f'),
... 	DataColumn('g'),
... 	RowidColumn('i'),
... )
>>> _ = mydb.test_types.insert(a=1, b=2, c=3, e=datetime.datetime(1969, 10, 5), f=6, g=7)
>>> for row in mydb.test_types.select():
...   print row
Row(a=1, b=True, c=u'3', e=datetime.datetime(1969, 10, 5, 0, 0), f=6.0, g='7', i=1)

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
#>>> mydb = DB()
>>> mydb.define_table('test_table', IntColumn('key'), StrColumn('value'))

>>> mydb.define_table('test_table_x', IntColumn('key'), primarykey=[])

Insert adds a row to the table.
>>> mydb.test_table.insert(key='100', value='a')

Rows can be fetched by primarykey. If no primarykeys are specified, an auto-
increment column is implicitly available. Autoincrement fields start from 1
>>> row = mydb.test_table[1]
>>> row.key
100
>>> row.value
u'a'
>>> row.rowid
1
>>> del mydb.test_table[1]

===
Consistency
===

The database acts as a context manager which controls data integrity. If several
operations need to be treated atomically:

If an error is raised, and the database driver supports transactions, all of the
operations in the current transaction are rolled back. Only the outer-most
context manager commits the transaction. Individual calls that modify
the database are wrapped in their own context managers, so they are committed
automatically.
>>> with mydb:
...   if 'transactions' in mydb.__driver__.features:
...     mydb.test_table.insert(key=3, value='c')
...     mydb.test_table.insert(key=4, value='d')
...   raise Exception
Traceback (most recent call last):
 ...
Exception
>>> list(mydb.test_table.select())
[]

>>> with mydb:
...   _ = mydb.test_table.insert(key=3, value='c')
...   _ = mydb.test_table.insert(key=7, value='g')
>>> for row in mydb.test_table.select():
...   print row
Row(key=3, value=u'c')
Row(key=7, value=u'g')

===
Querying
===

Doing comparison, binary or arithmetic operations on columns produces 'Where'
objects.
>>> mydb.test_table.key <= 3
Where([LESSEQUAL, 'test_table'.'key', 3])

The resulting object can be queried. Standard SQL commands are provided. Using
parentheses, a query can be set up and then selected:
>>> for row in (mydb.test_table.key<=3).select():
...   print row
Row(key=3, value=u'c')

Rows in a query can be counted...
>>> (mydb.test_table.key>1).count()
2

or updated...
>>> (mydb.test_table.value=='c').update(key=4)
>>> for row in mydb.test_table.select():
...   print row
Row(key=4, value=u'c')
Row(key=7, value=u'g')

or deleted...
>>> (mydb.test_table.key > 5).delete()
>>> for row in mydb.test_table.select():
...   print row
Row(key=4, value=u'c')

>>> _ = mydb.test_table.insert(key=4, value='d')
>>> _ = mydb.test_table.insert(key=5, value='d')

Multiple conditions can be combined using bitwise operators & and |
>>> (mydb.test_table.key == 4).count()
2
>>> (mydb.test_table.rowid < 0).count()
0
>>> ((mydb.test_table.rowid < 0) | (mydb.test_table.key == 4)).count()
2
>>> ((mydb.test_table.rowid < 0) & (mydb.test_table.key == 4)).count()
0

>>> for row in mydb.test_table.select(mydb.test_table.value, orderby=mydb.test_table.value, distinct=True):
...   print row.value
c
d

Order by one column
>>> for row in mydb.test_table.select(orderby=mydb.test_table.rowid):
...   print row
Row(key=4, value=u'c')
Row(key=4, value=u'd')
Row(key=5, value=u'd')

Or more
>>> for row in mydb.test_table.select(orderby=[reversed(mydb.test_table.key), mydb.test_table.value]):
...   print row
Row(key=5, value=u'd')
Row(key=4, value=u'c')
Row(key=4, value=u'd')

===
Cleaning Up
===

Remove tables by calling 'drop' on them.
>>> mydb.test_table.drop()
>>> mydb.test_types.drop()
"""
import collections
import copy
import datetime
import inspect
import sys

from . import drivers
from .drivers.base import timestamp, AuthenticationError

from .. import *

class __Row__(tuple):
	"""Base class for Row objects - elements of Selection objects
	
	"""
	__slots__ = ()

	@property
	def primarykey(self):
		return tuple(self[c.name] for c in self._selection.primarykey)

	def _asdict(self):
		return dict((k.name,self[k.name]) for k in self._selection.columns)
	__dict__ = property(_asdict)
		
	def update(self, **kwargs):
		'''Shortcut for updating a single row of the table
		'''
		if not self._selection.primarykey:
			raise RecordError("Can only manipulate records from a single table")
		table = self._selection.columns[0].table
		query = (table._by_pk(self.primarykey))
		query.update(**kwargs)
		return query.select().one()
		
	def __iter__(self):
		for i in range(len(self._selection.explicit)):
			yield self[i]
		
	def __getitem__(self, key):
		try:
			return tuple.__getitem__(self, key)
		except TypeError:
			return tuple.__getitem__(self, self._selection.index(key))
	__getattr__ = __getitem__
			
	def __len__(self):
		return len(self._selection.explicit)
		
	def __repr__(self):
		return 'Row(%s)'%', '.join('%s=%r'%(k.name,v) for k,v in zip(self._selection.explicit,self))

class Selection(object):
	def __init__(self, columns, explicit, primarykey, values):
		refs = {'__slots__':(),'_selection':self}
		if primarykey and primarykey[0].table._referers:
			refs.update({
				col.table._name:property(lambda row:(col==col.todb(row))) \
				for col in primarykey[0].table._referers
			})
		self.columns = columns # self.columns == self.explicit + self.primarykey
		self.explicit = explicit
		self.primarykey = primarykey
		self.names = {getattr(c,'name',None):i for i,c in enumerate(columns)}
		self.values = values
		self.Row = type('Row', (__Row__,), refs)

	def index(self, name):
		return self.names[name]
		
	def __iter__(self):
		def conv(c,v):
			try:
				if isinstance(v,c.native_type) or v is None:
					return v
				else:
					return c.native_type(v)
			except TypeError:
				print >>sys.stderr, c, v
				raise
		for value in self.values:
			yield self.Row(v if v is None else conv(c,(c.fromdb or ident)(v)) for c,v in zip(self.columns,value))

	def __contains__(self, seq):
		if hasattr(seq, 'items'):
			for row in self:
				if kwargs < row.as_dict():
					return True
			return False
		else:
			seq = sequence(seq)
			for row in self:
				if row[:len(seq)] == seq:
					return True
			return False
			
	def one(self):
		try:
			return iter(self).next()
		except StopIteration:
			return None

class Expression(object):
	def _op_args(self, op, *args):
		return [op] + map(lambda x:getattr(x,'_where_tree',x), args)
	def __nonzero__(self):
		return True

	def __eq__(self, x):
		return Where(self, drivers.base.EQUAL, self, x)
	def __ne__(self, x):
		return Where(self, drivers.base.NOTEQUAL, self, x)
	def __le__(self, x):
		return Where(self, drivers.base.LESSEQUAL, self, x)
	def __ge__(self, x):
		return Where(self, drivers.base.GREATEREQUAL, self, x)
	def __lt__(self, x):
		return Where(self, drivers.base.LESSTHAN, self, x)
	def __gt__(self, x):
		return Where(self, drivers.base.GREATERTHAN, self, x)
	
	def __add__(self, x):
		if isinstance(x, basestring) or \
		self.native_type in {str,bytes,unicode} or \
		x.native_type in {str,bytes,unicode}:
			self._text_affinity = True
			return Where(self, drivers.base.CONCATENATE, self, x)
		else:
			return Where(self, drivers.base.ADD, self, x)
	def __sub__(self, x):
		return Where(self, drivers.base.SUBTRACT, self, x)
	def __mul__(self, x):
		return Where(self, drivers.base.MULTIPLY, self, x)
	def __div__(self, x):
		return Where(self, drivers.base.DIVIDE, self, x)
	def __floordiv__(self, x):
		return Where(self, drivers.base.FLOORDIVIDE, self, x)
	def __div__(self, x):
		return Where(self, drivers.base.DIVIDE, self, x)
	def __truediv__(self, x):
		return Where(self, drivers.base.DIVIDE, self, x)
	def __mod__(self, x):
		return Where(self, drivers.base.MODULO, self, x)

	def __and__(self, x):
		return Where(self, drivers.base.AND, self, x)
	def __or__(self, x):
		return Where(self, drivers.base.OR, self, x)

	def __invert__(self):
		return Where(self, drivers.base.NOT, self)
	def __abs__(self):
		return Where(self, drivers.base.ABS, self)
	def __neg__(self):
		return Where(self, drivers.base.NEGATIVE, self)

	def length(self):
		return Where(self, drivers.base.LENGTH, self)
	def __reversed__(self):
		return Where(self, drivers.base.DESCEND, self)
		
	def sum(self):
		return Where(self, drivers.base.SUM, self)
	def average(self):
		return Where(self, drivers.base.AVERAGE, self, native_type=float)
	def min(self):
		return Where(self, drivers.base.MIN, self)
	def max(self):
		return Where(self, drivers.base.MAX, self)
	def round(self, precision=None):
		if precision is None:
			return Where(self, drivers.base.ROUND, self)
		else:
			return Where(self, drivers.base.ROUND, self, precision)

	def like(self, pattern, escape=None):
		if escape:
			return Where(self, drivers.base.LIKE, self, pattern, escape)
		else:
			return Where(self, drivers.base.LIKE, self, pattern)
	def glob(self, pattern):
		return Where(self, drivers.base.GLOB, self, pattern)
		
	def strip(self):
		return Where(self, drivers.base.STRIP, self)
	def lstrip(self):
		return Where(self, drivers.base.LSTRIP, self)
	def rstrip(self):
		return Where(self, drivers.base.RSTRIP, self)
	def replace(self, old, new):
		return Where(self, drivers.base.REPLACE, self, old, new)
	def endswith(self, suffix):
		return self[-len(suffix):] == suffix
	def startswith(self, prefix):
		return self[:len(prefix)] == prefix
	def __getitem__(self, index):
		if isinstance(index, slice):
			start = (index.start or 0)
			if start >= 0:
				start += 1
			if index.step not in (None, 1):
				raise ValueError('Slices of db columns must have step==1')
			if index.stop is None:
				return Where(self, drivers.base.SUBSTRING, self, start)
			elif index.stop >= 0:
				return Where(self, drivers.base.SUBSTRING, self, start, index.stop-start+1)
			else:
				raise ValueError('Negative-valued slices not allowed')
		return Where(self, drivers.base.SUBSTRING, self, index+1, 1)
		
	def coalesce(self, *args):
		return Where(self, drivers.base.COALESCE, self, *args)
	def between(self, min, max):
		return Where(self, drivers.base.BETWEEN, self, min, max)

class Where(Expression):
	def __init__(self, old, *wrapped, **kwargs):
		self._db = old._db
		if isinstance(old, Table):
			self._tables = {old}
			self._text_affinity = False
			self._where_tree = []
			self.todb = None
			self.fromdb = None
			self.native_type = None
		else:
			self._tables = old._tables
			self._where_tree = old._op_args(*wrapped)
			self.todb = kwargs.get('todb', old.todb)
			self.fromdb = kwargs.get('fromdb', old.fromdb)
			self.native_type = kwargs.get('native_type', old.native_type)

	def _get_columns(self, columns):
		if not columns:
			columns = [table.ALL for table in self._tables]
		return flatten(columns)
		
	def select(self, *columns, **props):
		columns = self._get_columns(columns)
		all_columns = columns[:]
		primarykey = []
		if not self._tables:
			raise Exception('No tables! Using %s' % flatten(columns))
		elif len(self._tables) == 1 and not props.get('distinct'):
			primarykey = self._tables.copy().pop().primarykey
			all_columns.extend(primarykey)
		values = self._db.__driver__._select(all_columns, self._tables, self._where_tree, props.get('distinct',False), sequence(props.get('orderby',())))
		return Selection(all_columns, columns, primarykey, values)
		
	def count(self, **props):
		columns = flatten(table.primarykey for table in self._tables)
		values = self._db.__driver__._select(columns, self._tables, self._where_tree, props.get('distinct',False), sequence(props.get('orderby',())))
		return len(values.fetchall())
		
	def update(self, **values):
		self._db.__driver__._update(self._tables.copy().pop()._name, self._where_tree, values)
		
	def delete(self):
		self._db.__driver__._delete(self._tables.copy().pop()._name, self._where_tree)
		
	def __repr__(self):
		return 'Where(%r)'%self._where_tree

ident = lambda x:x

class Column(Expression):
	"""Object representing a single column in a database table.

	:``name``: Name of the column. Must consist only of alpha-numerics
	  and underscores.
	:``native_type``: Python type which database should expect and
	  produce. Must be one of ``int``, ``bool``, ``float``, ``unicode``,
	  ``bytes``, or ``datetime.datetime``. This value is used by the
	  database driver to determine the type affinity of the database
	  column.
	:``todb=None``: Function which converts a value to ``native_type``
	  for passing to the database driver. If ``todb`` is ``None``, the
	  value is passed through unaltered.
	:``fromdb=None``: Function which converts a ``native_type`` value
	  from the database to the desired type. If ``fromdb`` is ``None``,
	  the native_type is returned unaltered.
	:``required=False``: Boolean value which determines whether a value
	  must be given on insert or update. ``None`` is not allowed as a
	  value of required columns.
	:``default=None``: Value to insert when no value is specified for
	  this column. This value is ignored if ``required`` is true. If
	  ``default`` is callable, it will be called with no arguments
	  every time an insert is performed and the return value will be
	  used instead.
	:``unique=False``: Boolean value. If true, no value (except
	  ``None``) can occur more than once in this column.
	:``primarykey=False``: Boolean value. If true, the values of this
	  column uniquely identify a row (possibly in combination with other
	  columns). A true value for ``primarykey`` implies ``unique=True``
	  and ``required=True``.
	:``references=None``: For any ``table``, values in this column (or
	  the result of this column's ``todb`` function) refer to
	  corresponding rows in ``table``. It is recommeded to use
	  ``ReferenceColumn`` to properly setup such references.
	:``length``: Integer specifying the expected maximum length of this
	  column's values. Please note that this limit is only enforced by
	  the database itself, so database engines that don't enforce size
	  limits (e.g. sqlite) might store longer values. In order to
	  enforce a strict length limit, use a ``todb`` function to truncate
	  values. For example, ``todb=lambda x:x[:24]``
	:``autoincrement=False``: Boolean value. If true, an
	  incrementally-increasing integer value is inserted by default by
	  the database.
	"""
	def __init__(self, name, native_type, todb=None, fromdb=None, required=False,
	default=None, unique=False, primarykey=False, references=None, length=None,
	autoincrement=False):
		self.name = name
		self.table = None
		self.native_type = native_type
		self.todb = todb
		self.fromdb = fromdb
		self.required = bool(required)
		self.default = default
		self.unique = bool(unique)
		self.primarykey = bool(primarykey)
		self.references = references
		self.length = length
		self.autoincrement = bool(autoincrement)

	@property
	def _tables(self):
		return {self.table}

	@property
	def _db(self):
		return self.table._db
		
	def __repr__(self):
		if self.table:
			return '%r.%r' % (self.table._name, self.name)
		else:
			return repr(self.name)

def RowidColumn(name, *args, **kwargs):
	kwargs['primarykey'] = True
	kwargs['autoincrement'] = True
	return Column(name, int, *args, **kwargs)

def IntColumn(name, *args, **kwargs):
	return Column(name, int, *args, **kwargs)

def BoolColumn(name, *args, **kwargs):
	return Column(name, bool, *args, **kwargs)

def StrColumn(name, *args, **kwargs):
	return Column(name, unicode, *args, **kwargs)

def FloatColumn(name, *args, **kwargs):
	return Column(name, float, *args, **kwargs)

def DataColumn(name, *args, **kwargs):
	return Column(name, bytes, *args, **kwargs)

def DateTimeColumn(name, *args, **kwargs):
	kwargs['todb'] = timestamp
	kwargs['fromdb'] = timestamp.parse
	return Column(name, datetime.datetime, *args, **kwargs)

def ReferenceColumn(name, table, todb=None, *args, **kwargs):
	kwargs['references'] = table
	if not todb:
		if len(table.primarykey) == 1:
			todb = lambda row:row.primarykey[0]
		elif len(table.primarykey) == 0:
			raise TypeError("Cannot reference non-indexed table %r" % table._name)
		else:
			raise ValueError("Default ReferenceColumn todb function supports only 1 primary key.")
	query = todb(table)
	kwargs['todb'] = todb
	kwargs['fromdb'] = query.fromdb
	self = Column(name, query.native_type, *args, **kwargs)
	table._referers.add(self)
	return self

class Table(object):
	"""

	self._columns: collection of all column objects
	self.ALL: list of columns the user defined (excludes implicit or primarykey-only
	  columns
	self.primarykey: list of columns which together uniquely identify a row in
	  the table
	self._db: reference to db which contains this table
	self._name: my name

	>>> Table(None, 'table', ())
	<Table 'table'>
	>>> t = Table(None, 'table', [Column('abc', str), Column('def', int)])
	>>> t.ALL[0].table == t
	True
	>>> t.ALL[0].name
	'abc'
	>>> t.ALL[1].name
	'def'
	>>> t.primarykey[0].name
	'rowid'
	"""
	def __init__(self, db, name, columns, primarykey=None):
		self._db = db
		self._name = name
		self.ALL = columns
		self._columns = collection('name', columns)
		self._referers = set()
		if primarykey is None:
			pk = [c for c in columns if c.primarykey]
			if pk:
				self.primarykey = pk
			else:
				rowid = RowidColumn('rowid')
				self._columns.add(rowid)
				self.primarykey = [rowid]
		else:
			self.primarykey = []
			if primarykey:
				for col in primarykey:
					if isinstance(col, basestring):
						col = self._columns[col]
					else:
						self._columns.add(col)
					self.primarykey.append(col)
		for col in self._columns:
			col.table = self

	def __getattr__(self, key):
		if key in self.__dict__:
			return self.__dict__[key]
		else:
			return self._columns[key]
		
	def __hash__(self):
		return hash(self._name)

	def _by_pk(self, key):
		if self.primarykey:
			key = sequence(key)
			if len(self.primarykey) != len(key):
				raise IndexError('Primarykey for %s requires %i values (got %i)' % (self._name, len(self.primarykey), len(key)))
			assert len(self.primarykey) == len(key)
			selection = self.primarykey[0] == key[0]
			for k,v in zip(self.primarykey[1:], key[1:]):
				selection &= k==v
			return selection
		raise TypeError('Table %r has no primarykey' % (self._name))

	def __getitem__(self, key):
		result = self._by_pk(key).select(self.ALL).one()
		if result is None:
			raise KeyError('No Row in database matching primary key %s'%repr(sequence(key))[1:-1])
		return result

	def __delitem__(self, key):
		self._by_pk(key).delete()

	def insert(self, **values):
		db_values = []
		for k,v in values.items():
			try:
				todb = self._columns[k].todb
				if todb:
					v = todb(v)
				db_values.append(v)
			except TypeError:
				print >>sys.stderr, k, self._columns[k].todb, repr(v)
				raise
			except KeyError:
				raise KeyError('No such column in table: %s' % k)
		self._db.__driver__._insert(self._name, values.keys(), db_values)

	def insert_many(self, *records):
		for record in records:
			self.insert(**record)

	def select(self, *columns, **props):
		return Where(self).select(*(columns or self.ALL), **props)
		
	def drop(self):
		self._db.__driver__.drop_table(self._name)
		del self._db[self._name]

	def __repr__(self):
		return '<%s %r>' % (self.__class__.__name__, self._name)
		
	def __nonzero__(self):
		return True

	def __eq__(self, x):
		if isinstance(x, Table):
			x = x._columns
		for a,b in zip(self._columns, x):
			a = dict(vars(a))
			a.pop('table', None)
			b = dict(vars(b))
			b.pop('table', None)
			if a != b:
				return False
		return True

class UnknownDriver(Exception): pass

class DB(collection):
	"""
	
	>>> mydb = DB.connect('sqlite')
	>>> mydb.define_table('test', StrColumn('data'))
	>>> list(mydb)
	[<Table 'test'>]
	"""
	__driver__ = drivers.sqlite.sqlite()
	execute = __driver__.execute

	@property
	def lastsql(self):
		return self.__driver__.lastsql

	def __init__(self):
		collection.__init__(self, namekey='_name')
		
	def __enter__(self):
		self.__driver__.__enter__()
		
	def __exit__(self, obj, exc, tb):
		self.__driver__.__exit__(obj, exc, tb)

	def define_table(self, name, *columns, **kwargs):
		columns = list(columns)
		primarykey = ()
		for i,c in enumerate(columns):
			if isinstance(c,Table):
				newcols = map(copy.copy, c.ALL)
				for col in newcols:
					col.table = None
				columns[i] = newcols
				primarykey = map(copy.copy, c.primarykey)
				for col in primarykey:
					col.table = None
		if primarykey and kwargs.get('primarykey') is None:
			kwargs['primarykey'] = primarykey
		elif kwargs.get('primarykey'):
			kwargs['primarykey'] = sequence(kwargs['primarykey'])
		value = Table(self, name, flatten(columns), **kwargs)
		self.__driver__._create_table_if_nexists(name, value._columns, [pk.name for pk in value.primarykey])
		collection.__setitem__(self, name, value)

	def __getattr__(self, key):
		return self.__dict__[key] if key[0] == '_' else self[key]
	
	def __delattr__(self, key):
		if key[0] == '_':
			del self.__dict__[key]
		else:
			del self[key]

	@classmethod
	def connect(cls, name, *args, **kwargs):
		try:
			driver = getattr(getattr(drivers, name), name)
		except AttributeError:
			raise UnknownDriver("Unable to find database driver %r" % name)
		driver = driver(*args,**kwargs)
		return type(cls.__name__, (cls,), {
			'__driver__':driver,
			'execute':driver.execute,
		})()

	def conform(self):
		"""DB.conform()
		
		Reads database for table definitions"""
		for table in self.__driver__.list_tables():
			columns = []
			for name,v_type,notnull,default in self.__driver__._list_columns(table):
				columns.append(Column(name, v_type, required=notnull, default=default))
			t = Table(self, table, columns)
			collection.add(self, t)
		
	def migrate(self):
		"""DB.migrate()
		
		Alters database to match defined tables"""
		names = set(self.keys())
		db_tables = set(self.__driver__.list_tables())
		for name in names - db_tables:
			#Create
			self.__driver__._create_table_if_nexists(name, self[name])
		for name in names.intersection(db_tables):
			#Alter if not the same
			raise NotImplementedError
			self.__driver__.alter_table(name, self[name])

connect = DB.connect
