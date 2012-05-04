"""

Open a database connection. An in-memory database is created with
>>> mydb = DB()

otherwise use the connect method
>>> mydb = DB.connect('sqlite','/tmp/webdb.doctest.sqlite')

Tables are defined by assigning them to attributes of a database. Two special
methods help with definitions.

Conform reads table definitions from the database, overriding any tables
that have already been defined.
>>> mydb.conform()

>>> mydb.test_table = Table(Field('key'), Field('value'))
>>> mydb.test_table = Table(Field('key'), Field('value'), Field('extra'))
>>> mydb.test_table
Table(Field('key', 'string'), Field('value', 'string'), Field('extra', 'string'))
>>> mydb.conform()
>>> mydb.test_table
Table(Field('key', 'string'), Field('value', 'string'))
>>> mydb.test_table = Table(Field('key'), Field('value'), Field('extra'))

Migrate modifies tables in the database to be like newly-assigned tables.
>>> mydb.migrate()
>>> mydb.test_table
Table(Field('key', 'string'), Field('value', 'string'), Field('extra', 'string'))
"""
import collections
import inspect
import drivers.sqlite

class Row(object):
	pass

class Selection(object):
	pass
	
class Set(object):
	pass

class Field(object):
	'''Field(name, type='string', notnull=False, default=None)
	
	valid types:
	'string' or basestring
	'text'
	'integer' or int
	'boolean' or bool
	'''
	def __init__(self, name, type='string', notnull=False, default=None):
		self.name = name
		self.type = type
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
		return 'Field%i(%s)' % (self.index,', '.join(values))
		
	def __cmp__(self, x):
		return cmp(self.index, x.index)

class Table(object):
	def __init__(self, *fields, **kwargs):
		id_field = kwargs.get('id_field')
		for i,f in enumerate(fields):
			if f.index is None:
				f.index = i+1
			self.__dict__[f.name] = f
			
	def fields(self):
		return vars(self).values()
		
	def __repr__(self):
		return 'Table(%s)' % ', '.join(map(repr,sorted(vars(self).values())))

class DB(collections.Mapping):
	"""
	
	>>> mydb = DB.connect('sqlite')
	>>> mydb.test = Table(Field('data'))
	>>> list(mydb.tables())
	[Table(Field('data', 'string'))]
	"""
	__driver__ = drivers.sqlite.sqlite()
	
	def __setattr__(self, key, value):
		#Create a table if it's new
		assert isinstance(value, Table)
		super(DB, self).__setattr__(key, value)
		self.__driver__.create_table_if_nexists(key, value)
		
	def __getitem__(self, key):
		return self.__dict__[key]
		
	def __setitem__(self, key, value):
		self.__dict__[key] = value
	
	def __delitem__(self, key):
		del self.__dict__[key]

	def __iter__(self):
		return iter(self.__dict__)
		
	def __len__(self):
		return len(self.__dict__)
		
	def tables(self):
		return self.values()
		
	@classmethod
	def connect(cls, name, *args, **kwargs):
		driver = getattr(__import__('drivers.%s'%name, fromlist=name), name)
		newcls = type(cls.__name__, (cls,), {'__driver__':driver(*args,**kwargs)})
		return newcls()
		
	def conform(self):
		for table in self.__driver__.list_tables():
			fields = []
			for idx,name,v_type,notnull,default in self.__driver__.list_columns(table):
				fields.append(Field(name, v_type, notnull=notnull, default=default))
			self.__dict__[table] = Table(*fields)
		
	def migrate(self):
		pass

if __name__=='__main__':
	import doctest
	doctest.testmod()
