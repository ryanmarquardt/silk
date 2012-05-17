
from webdoc import container
import sqlite3
import errno

class ColumnError(Exception): pass

class op(object):
	def __repr__(self):
		return self.__class__.__name__
	def __eq__(self, x):
		return isinstance(x, self.__class__)
class EQUAL(op): pass
EQUAL = EQUAL()
class NOTEQUAL(op): pass
NOTEQUAL = NOTEQUAL()
class LESSTHAN(op): pass
LESSTHAN = LESSTHAN()
class LESSEQUAL(op): pass
LESSEQUAL = LESSEQUAL()
class GREATERTHAN(op): pass
GREATERTHAN = GREATERTHAN()
class GREATEREQUAL(op): pass
GREATEREQUAL = GREATEREQUAL()
class ADD(op): pass
ADD = ADD()
class CONCATENATE(op): pass
CONCATENATE = CONCATENATE()
class SUBTRACT(op): pass
SUBTRACT = SUBTRACT()
class MULTIPLY(op): pass
MULTIPLY = MULTIPLY()
class DIVIDE(op): pass
DIVIDE = DIVIDE()
class FLOORDIVIDE(op): pass
FLOORDIVIDE = FLOORDIVIDE()
class MODULO(op): pass
MODULO = MODULO()
class AND(op): pass
class OR(op): pass
class NOT(op): pass

class driver_base(object):
	def __init__(self, connection):
		self.connection = connection
		self.depth = 0
		self.cursor = None

	def create_table_if_nexists(self, name, table):
		if name not in self.list_tables:
			self.create_table(name, table)

	def __enter__(self):
		self.depth += 1
		if self.cursor is None:
			self.cursor = self.connection.cursor()
		return self.cursor
		
	def __exit__(self, obj, exc, tb):
		self.depth -= 1
		if self.depth == 0:
			if obj:
				self.connection.rollback()
			else:
				self.connection.commit()
			self.cursor = None
		
	def execute(self, sql, values=()):
		self.lastsql = sql
		with self as cursor:
			return cursor.execute(sql, values)
		
	def validate_name(self, name):
		if not name.replace('_','').isalnum():
			raise ColumnError("Column names can only contain letters, numbers, and underscores. Got %r" % name)

class sqlite(driver_base):
	"""Driver for sqlite3 databases

	sqlite accepts only one parameter: path, which is the path of the database
	file. By default, path=':memory:', which creates a temporary database
	in memory.
	"""
	def __init__(self, path=':memory:'):
		self.path = path
		try:
			driver_base.__init__(self, sqlite3.connect(path))
		except sqlite3.OperationalError, e:
			if e.message == 'unable to open database file':
				e = IOError(errno.ENOENT, 'No such file or directory: %r' % path)
				e.errno = errno.ENOENT
			raise e
			
	operators = {
		EQUAL:lambda a,b:'%s=%s'%(a,b),
		LESSEQUAL:lambda a,b:'%s<=%s'%(a,b),
		GREATERTHAN:lambda a,b:'%s>%s'%(a,b),
	}
	def protect_identifier(self, name):
		return '"%s"'%name
		
	def represent_literal(self, value):
		if isinstance(value, basestring):
			return "'%s'"%value.replace("'", "\'")
		else:
			return repr(value)
			
	def column_name(self, table, col):
		return '.'.join(map(self.protect_identifier, (table, col)))
		
	def parse_where(self, conditions):
		if isinstance(conditions, list):
			operator = conditions[0]
			return '(%s)'%self.operators[operator](*map(self.parse_where,conditions[1:]))
		elif hasattr(conditions, 'table') and hasattr(conditions, 'name'): #Column duck-typed
			return self.column_name(conditions.table._name, conditions.name)
		else:
			return self.represent_literal(conditions)
		
	def list_tables(self):
		return (str(n) for (n,) in self.execute("""SELECT name FROM sqlite_master WHERE type='table'"""))
		
	def list_columns(self, table):
		return ((str(name),self.unmap_type(v_type),bool(notnull),default) for (_,name,v_type,notnull,default,_) in self.execute("""PRAGMA table_info("%s");""" % table))
			
	def format_value(val, cast=None):
		if val is None:
			return 'NULL'
		elif cast in ('INT','REAL'):
			return "%g"%val
		elif cast in ('TEXT','BLOB'):
			return "'%s'"%str(val).replace("'", "''")
		else:
			return val
			
	def map_type(self, t):
		if t == 'rowid':
			return 'INTEGER PRIMARY KEY'
		elif t == 'string':
			return 'TEXT'
		elif t == 'text':
			return 'TEXT'
		elif t == 'integer':
			return 'INT'
		elif t == 'float':
			return 'REAL'
		elif t == 'data':
			return 'BLOB'
		elif t == 'boolean':
			return 'INT'
			
	def unmap_type(self, t):
		if t == 'TEXT':
			return 'string'
		elif t == 'INT':
			return 'integer'
		elif t == 'REAL':
			return 'float'
		elif t == 'BLOB':
			return 'data'

	def format_column(self, column):
		props = container(vars(column))
		self.validate_name(props.name)
		props.type = self.map_type(props.type)
		props.notnull = ' NOT NULL' if column.notnull else ''
		props.default = " DEFAULT %s"%self.format_value(column.default, props.type) if column.notnull or not column.default is None else ''
		return '"%(name)s" %(type)s%(notnull)s%(default)s' % props

	def create_table_if_nexists(self, name, table):
		self.validate_name(name)
		self.execute("""CREATE TABLE IF NOT EXISTS "%s"(%s);""" % (
			name,
			', '.join(map(self.format_column, table))
		))

	def create_table(self, name, table):
		self.validate_name(name)
		self.execute("""CREATE TABLE "%s"(%s);""" % (
			name,
			', '.join(map(self.format_column,table))
		))

	def rename_table(self, orig, new):
		self.validate_name(orig)
		self.validate_name(new)
		self.execute("""ALTER TABLE "%s" RENAME TO "%s";""" % (orig, new))

	def alter_table(self, name, table):
		self.validate_name(name)
		with self:
			db_cols = self.list_columns(name)
			db_names = [c[0] for c in db_cols]
			for column in table:
				if column.name not in db_names:
					self.execute("""ALTER TABLE "%s" ADD COLUMN %s;"""%(
						name, self.format_column(column)
					))

	def select(self, columns, conditions):
		tables = set()
		names = []
		for c in columns:
			tables.add(c.table._name)
			names.append((c.table._name,c.name))
		where = self.parse_where(conditions) if conditions else ''
		if where:
			where = ' WHERE '+where
		if len(tables) == 1:
			table = tables.pop()
			self.validate_name(table)
			#where = ' and '.join("%s.%s=%s"%(c.table._name,c.name,v) for (c,v) in conditions)
			sql = """SELECT %s FROM %s%s;""" % (
				', '.join(self.column_name(*i) for i in names),
				self.protect_identifier(table),
				where,
			)
			return self.execute(sql)
		else:
			raise Exception("Can't handle query with %i tables: %s" % (len(tables), where))

	def insert(self, values, table):
		self.validate_name(table)
		cur = self.execute("""INSERT INTO %s(%s) VALUES (%s)""" % (
			self.protect_identifier(table),
			','.join(values.keys()),
			','.join(list('?'*len(values))),
		), values.values())
		return cur.lastrowid

	def update(self, table, conditions, values):
		where = self.parse_where(conditions) if conditions else ''
		if where:
			where = ' WHERE '+where
		sql = """UPDATE %s SET %s%s;""" % (
			self.protect_identifier(table),
			', '.join('%s=?'%(self.protect_identifier(k)) for k in values.keys()),
			where,
		)
		return self.execute(sql, values.values())

	def delete(self, table, conditions):
		where = self.parse_where(conditions) if conditions else ''
		if where:
			where = ' WHERE '+where
		sql = """DELETE FROM %s%s;""" % (
			self.protect_identifier(table),
			where,
		)
		return self.execute(sql)
