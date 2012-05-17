
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
AND = AND()
class OR(op): pass
OR = OR()
class NOT(op): pass
NOT = NOT()
class NEGATIVE(op): pass
NEGATIVE = NEGATIVE()
class ABS(op): pass
ABS = ABS()

class driver_base(object):
	def __init__(self, connection):
		self.connection = connection
		self.depth = 0
		self.cursor = None

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
			try:
				return cursor.execute(sql, values)
			except sqlite3.OperationalError, e:
				raise Exception(e, sql, values)
		
	def identifier(self, name):
		if not name.replace('_','').isalnum():
			raise ColumnError("Column names can only contain letters, numbers, and underscores. Got %r" % name)
		return '"%s"'%name

	#def format_value(val, cast=None):
		#if val is None:
			#return 'NULL'
		#elif cast in ('INT','REAL'):
			#return "%g"%val
		#elif cast in ('TEXT','BLOB'):
			#return "'%s'"%str(val).replace("'", "''")
		#else:
			#return val
			

	def literal(self, value, cast=None):
		if value is None:
			return 'NULL'
		elif isinstance(value, basestring) or cast in ('TEXT','BLOB'):
			return "'%s'"%str(value).replace("'", "''")
		elif cast in ('INT', 'REAL'):
			return '%g'%value
		else:
			return value
			
	def column_name(self, table, col):
		return '.'.join(map(self.identifier, (table, col)))
		
	def parse_where(self, where_clause):
		if where_clause:
			def recurse(conditions):
				if isinstance(conditions, list):
					operator = conditions[0]
					return '(%s)'%self.operators[operator](*map(recurse,conditions[1:]))
				elif hasattr(conditions, 'table') and hasattr(conditions, 'name'): #Column duck-typed
					return self.column_name(conditions.table._name, conditions.name)
				else:
					return self.literal(conditions)
			clause = recurse(where_clause)
			if clause:
				clause = ' WHERE '+clause
		else:
			clause = ''
		return clause
		
	def format_column(self, column):
		props = container()
		props.name = self.identifier(column.name)
		props.type = self.map_type(column.type)
		props.notnull = ' NOT NULL' if column.notnull else ''
		props.default = " DEFAULT %s"%self.literal(column.default, props.type) if column.notnull or not column.default is None else ''
		return '%(name)s %(type)s%(notnull)s%(default)s' % props

	def map_type(self, t):
		r = self.webdb_types.get(t)
		if r:
			return r
		else:
			raise Exception('Unknown column type %s' % t)
			
	def unmap_type(self, t):
		r = self.driver_types.get(t)
		if r:
			return r
		else:
			raise Exception('Unknown column type %s' % t)


	def create_table_if_nexists(self, name, table):
		if hasattr(self, 'create_table_if_nexists_sql'):
			self.execute(self.create_table_if_nexists_sql(
				self.identifier(name),
				*map(self.format_column, table)
			))
		elif name not in self.list_tables:
			self.create_table(name, table)

	def create_table(self, name, table):
		self.execute(self.create_table_sql(self.identifier(name), map(self.format_column,table)))

	def list_tables(self):
		return (str(n) for (n,) in self.execute(self.list_tables_sql()))

	def rename_table(self, orig, new):
		self.execute(self.rename_table_sql(self.identifier(orig), self.identifier(new)))

	def alter_table(self, name, table):
		with self:
			db_cols = self.list_columns(name)
			db_names = [c[0] for c in db_cols]
			for column in table:
				if column.name not in db_names:
					self.execute(self.add_column_sql(self.identifier(name), self.format_column(column)))

	def select(self, columns, tables, conditions):
		return self.execute(self.select_sql([self.column_name(c.table._name, c.name) for c in columns], [self.identifier(t._name) for t in tables], self.parse_where(conditions)))

	def insert(self, table, values):
		cur = self.execute(self.insert_sql(self.identifier(table), map(self.identifier,values.keys())), values.values())
		return cur.lastrowid

	def update(self, table, conditions, values):
		return self.execute(self.update_sql(self.identifier(table), map(self.identifier,values.keys()), self.parse_where(conditions)), values.values())

	def delete(self, table, conditions):
		return self.execute(self.delete_sql(self.identifier(table), self.parse_where(conditions)))


class sqlite(driver_base):
	"""Driver for sqlite3 databases

	sqlite accepts only one parameter: path, which is the path of the database
	file. By default, path=':memory:', which creates a temporary database
	in memory.
	"""
	def __init__(self, path=':memory:'):
		self.path = path
		try:
			driver_base.__init__(self, sqlite3.connect(path, sqlite3.PARSE_DECLTYPES))
		except sqlite3.OperationalError, e:
			if e.message == 'unable to open database file':
				e = IOError(errno.ENOENT, 'No such file or directory: %r' % path)
				e.errno = errno.ENOENT
			raise e
			
	operators = {
		EQUAL:lambda a,b:'%s=%s'%(a,b),
		LESSEQUAL:lambda a,b:'%s<=%s'%(a,b),
		GREATERTHAN:lambda a,b:'%s>%s'%(a,b),
		NOTEQUAL:lambda a,b:'%s!=%s'%(a,b),
		LESSTHAN:lambda a,b:'%s<%s'%(a,b),
		GREATEREQUAL:lambda a,b:'%s>=%s'%(a,b),
		ADD:lambda a,b:'%s+%s'%(a,b),
		CONCATENATE:lambda a,b:'%s||%s'%(a,b),
		SUBTRACT:lambda a,b:'%s-%s'%(a,b),
		MULTIPLY:lambda a,b:'%s*%s'%(a,b),
		DIVIDE:lambda a,b:'%s/%s'%(a,b),
		FLOORDIVIDE:lambda a,b:'%s/%s'%(a,b),
		MODULO:lambda a,b:'%s%%%s'%(a,b),
		AND:lambda a,b:'%s AND %s'%(a,b),
		OR:lambda a,b:'%s OR %s'%(a,b),
		NOT:lambda a:'NOT %s'%a,
		NEGATIVE:lambda a:'-%s'%a,
	}
	
	webdb_types = {
		'rowid':'INTEGER PRIMARY KEY',
		'string':'TEXT',
		'integer':'INT',
		'float':'REAL',
		'data':'BLOB',
		'boolean':'INT',
		'datetime':'TIMESTAMP',
	}
	
	driver_types = {
		'TEXT':'string',
		'INT':'integer',
		'REAL':'float',
		'BLOB':'data',
		'TIMESTAMP':'datetime',
	}
	
	def list_tables_sql(self):
		return """SELECT name FROM sqlite_master WHERE type='table'"""
		
	def list_columns(self, table):
		for _,name,v_type,notnull,default,_ in self.execute("""PRAGMA table_info("%s");""" % table):
			yield (str(name),self.unmap_type(v_type),bool(notnull),default)
			

	def create_table_if_nexists_sql(self, name, *coldefs):
		return """CREATE TABLE IF NOT EXISTS %s(%s);""" % (name, ', '.join(coldefs))

	def create_table_sql(self, name, *coldefs):
		return """CREATE TABLE %s(%s);""" % (name, ', '.join(coldefs))

	def rename_table_sql(self, orig, new):
		return """ALTER TABLE %s RENAME TO %s;""" % (orig, new)

	def add_column_sql(self, table, column):
		return """ALTER TABLE %s ADD COLUMN %s;""" % (table, column)

	def select_sql(self, columns, tables, where):
		return """SELECT %s FROM %s%s;""" % (', '.join(columns), ', '.join(tables), where)

	def insert_sql(self, table, names):
		return """INSERT INTO %s(%s) VALUES (%s)""" % (table, ','.join(names), ','.join(list('?'*len(names))))

	def update_sql(self, table, names, where):
		return """UPDATE %s SET %s%s;""" % (table, ', '.join('%s=?'%n for n in names), where)

	def delete_sql(self, table, where):
		return """DELETE FROM %s%s;""" % (table, where)
