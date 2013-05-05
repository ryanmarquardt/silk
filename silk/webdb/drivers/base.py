
from ... import sequence, flatten
import sys
import datetime

def timestamp(arg):
	return arg.replace()

def parse(string):
	if string is None: return None
	elif not isinstance(string, (datetime.datetime, datetime.date, datetime.time)):
		return datetime.datetime.strptime(string, '%Y-%m-%d %H:%M:%S')
	else: return string
timestamp.parse = parse
del parse

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
class LENGTH(op): pass
LENGTH = LENGTH()
class ASCEND(op): pass
ASCEND = ASCEND()
class DESCEND(op): pass
DESCEND = DESCEND()
class SUM(op): pass
SUM = SUM()
class AVERAGE(op): pass
AVERAGE = AVERAGE()
class BETWEEN(op): pass
BETWEEN = BETWEEN()
class MIN(op): pass
MIN = MIN()
class MAX(op): pass
MAX = MAX()
class UPPER(op): pass
UPPER = UPPER()
class LOWER(op): pass
LOWER = LOWER()
class LIKE(op): pass
LIKE = LIKE()
class GLOB(op): pass
GLOB = GLOB()
class LSTRIP(op): pass
LSTRIP = LSTRIP()
class STRIP(op): pass
STRIP = STRIP()
class RSTRIP(op): pass
RSTRIP = RSTRIP()
class REPLACE(op): pass
REPLACE = REPLACE()
class ROUND(op): pass
ROUND = ROUND()
class SUBSTRING(op): pass
SUBSTRING = SUBSTRING()
class COALESCE(op): pass
COALESCE = COALESCE()


"""The silk DAL expects the following methods to be available from its driver:

driver.list_tables() -> list of names of tables in database

driver.list_columns(table) -> iterator of tuples(name, v_type, notnull, default)
  name: column name
  v_type: type name of column
  notnull: boolean
  default: default value
  
driver.rename_table(table, name) -> return value is ignored

driver.add_column(table, column) -> return value is ignored

driver.drop_column(table, column) -> return value is ignored

driver.create_table_if_nexists(name, columns, primarykeys) -> return value is ignored

driver.delete(table, where) -> return value is ignored
  table: table name
  where: where_tree

driver.drop_table(table) -> return value is ignored
  table: table name

driver.insert(table, columns, values) -> returns rowid of inserted row (integer > 0)
  table: table name
  values: dictionary of values to insert

driver.select(tables, columns, where, distinct, orderby) -> iterator over result set
  tables: set of table objects
  columns: list of column objects
  where: where object's "where_tree"; nested list like [operator, arg1, arg2, ...]
  distinct: distinct
  orderby: list of ordering columns
  
driver.update(table, columns, values, where) -> return value is ignored
  table: table name
  columns: list of columns to update
  values: list of values to set
  where: where_tree

driver.commit() -> return value is ignored
driver.rollback() -> return value is ignored
"""

class driver_base(object):
	'''Base class for database drivers
	
	This class abstracts away a lot of the logic needed to implement a database
	driver for webdb. Derived classes must overload the following methods to
	have a working driver. If the task is best accomplished using a single SQL
	command, the method ending in '_sql' should be defined, as the alternatives
	use those to accomplish their tasks. For more information, view documentation
	on each specific method
	
	  * list_tables or list_tables_sql
	     - list all tables in the database. Implements: db.conform
	  * list_columns or list_columns_sql
	     - list all columns defined in a table. Implements: db.conform
	  * create_table, create_table_sql, create_table_if_nexists,
	    or create_table_if_nexists_sql
	     - create tables (if missing). Implements: db.__setattr__, db.migrate
	  * rename_table or rename_table_sql.
	     - changes a table's name. Implements: db.migrate
	  * add_column or add_column_sql
	     - adds a new column to a table. Implements: db.migrate
	  * select or select_sql
	     - retrieves rows from a table. Implements: Where.select, table.select
	  * insert or insert_sql
	     - adds rows to a table. Implements: table.insert
	  * update or update_sql
	     - alters records in a table. Implements: Where.update, row.update
	  * delete or delete_sql
	     - removes records from a table. Implements: Where.delete, row.delete,
	       table.__delitem__, table.__delattr__
	
	Additionally, the following variables must be defined.
	
	  * webdb_types: a dictionary mapping webdb column types to names of database
	      column types. Used for defining tables
	  * driver_types: a dictionary mapping database column types to webdb column
	      types. Used when conforming.
	
	The following methods should be defined by subclasses if the database uses
	non-standard syntax
	
	  * identifier
	     - checks that a table or column name uses valid characters, and is properly
	       escaped (to avoid keywords). Default encloses name in double quotes (")
	  * literal
	     - formats a literal value to be used in an sql expression. 
	  * column_name
	     - returns the name of a column. Default returns dot (.) joined result
	       of identifier on its arguments, i.e. "table"."column" 
	  * format_column
	     - returns a column definition for its Column object argument

	The following methods may be defined by subclasses, but are not required for
	normal use.
	
	  * drop_column or drop_column_sql
	     - removes a column and all its data from a table. Columns in a table
	       which don't appear in a table definition are ignored.
	       Implements: table.drop_column
	'''

	def __init__(self, connection, debug=False):
		self.connection = connection
		self.depth = 0
		self.cursor = None
		self.debug = debug
		self.features = {'transactions'}

	def __enter__(self):
		self.depth += 1
		if self.cursor is None:
			self.cursor = self.connection.cursor()
		return self.cursor
		
	def __exit__(self, obj, exc, tb):
		self.depth -= 1
		if self.depth == 0:
			if obj:
				self.rollback()
			else:
				self.commit()
			self.cursor = None

	def commit(self):
		self.connection.commit()

	def rollback(self):
		self.connection.rollback()
		
	def execute(self, sql, values=()):
		self.lastsql = sql
		#print >>sys.stderr, sql, values or ''
		with self as cursor:
			try:
				cursor.execute(sql, values)
				return cursor
			except Exception, e:
				self.handle_exception(e)
				raise Exception(e, sql, values)

		
	def identifier(self, name):
		if not name.replace('_','').isalnum():
			raise NameError("Column names can only contain letters, numbers, and underscores. Got %r" % name)
		return '"%s"'%name

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
	
	def expression(self, x):
		if isinstance(x, list):
			operator = x[0]
			return '(%s)'%getattr(self,'op_%s'%operator)(*map(self.expression,x[1:]))
		elif hasattr(x, 'table') and hasattr(x, 'name'): #Column duck-typed
			return self.column_name(x.table._name, x.name)
		elif hasattr(x, '_where_tree'): #Where duck-typed
			return self.expression(x._where_tree)
		else:
			return self.literal(x)
		
	def parse_where(self, where_clause):
		if where_clause:
			clause = self.expression(where_clause)
			if clause:
				clause = ' WHERE '+clause
		else:
			clause = ''
		return clause
		
	def format_column(self, column):
		type = self.map_type(column.native_type)
		if type is None:
			raise Exception('Unknown column type %s' % column.native_type)
		default = " DEFAULT %s"%self.literal(column.default, type) if not callable(column.default) and (column.required or not column.default is None) else ''
		return '%(name)s %(type)s%(notnull)s%(autoinc)s%(default)s' % {
			'name': self.identifier(column.name),
			'type': type,
			'notnull': ' NOT NULL' if column.required else '',
			'default': default,
			'autoinc': ' AUTO_INCREMENT' if column.autoincrement else ''
		}

	def map_type(self, t):
		r = self.webdb_types.get(t)
		if r:
			return r
			
	def unmap_type(self, t):
		r = self.driver_types.get(t)
		if r:
			return r


	def list_tables(self):
		return (str(n) for (n,) in self.execute(self.list_tables_sql()))

	def list_tables_sql(self):
		raise NotImplementedError

	def list_columns(self, table):
		raise NotImplementedError

	def rename_table(self, table, name):
		self.execute(self.rename_table_sql(self.identifier(table), self.identifier(name)))

	def rename_table_sql(self, table, name):
		raise NotImplementedError

	def add_column(self, table, column):
		with self:
			db_cols = self.list_columns(name)
			db_names = [c[0] for c in db_cols]
			for column in table.columns:
				if column.name not in db_names:
					self.execute(self.add_column_sql(self.identifier(name), self.format_column(column)))

	def add_column_sql(self, table, column):
		raise NotImplementedError

	def drop_column(self, table, column):
		raise NotImplementedError

	def create_table_if_nexists(self, name, columns, primarykeys):
		if hasattr(self, 'create_table_if_nexists_sql'):
			self.execute(self.create_table_if_nexists_sql(
				self.identifier(name),
				map(self.format_column, columns),
				map(self.identifier, primarykeys),
			))
		elif name not in self.list_tables:
			self.create_table(name, columns, primarykeys)

	def create_table_if_nexists_sql(self, name, columns, primarykeys):
		'''create_table_if_nexists_sql(self, name, *columns) -> Stub
		
		Base classes should return SQL for creating a table if it doesn't
		exist. All arguments are already formatted as strings.'''
		raise NotImplementedError

	def create_table_sql(self, name, columns):
		raise NotImplementedError

	def create_table(self, name, columns, primarykeys):
		try:
			self.execute(self.create_table_sql(self.identifier(name), map(self.format_column,columns), primarykeys))
		except NotImplementedError:
			self.create_table_if_nexists(name, table.columns)

	def delete(self, table, conditions):
		return self.execute(self.delete_sql(self.identifier(table), self.parse_where(conditions)))

	def delete_sql(self, table, conditions):
		raise NotImplementedError

	def drop_table(self, table):
		self.execute(self.drop_table_sql(self.identifier(table)))

	def drop_table_sql(self, table):
		raise NotImplementedError

	def insert(self, table, columns, values):
		cur = self.execute(self.insert_sql(self.identifier(table), map(self.identifier,columns)), values)
		return cur.lastrowid

	def insert_sql(self, table, columns):
		raise NotImplementedError

	def select(self, columns, tables, conditions, distinct, orderby):
		return self.execute(self.select_sql(
			map(self.expression,columns),
			[self.identifier(t._name) for t in tables],
			self.parse_where(conditions),
			bool(distinct),
			orderby,
		))

	def select_sql(self, columns, tables, conditions, distinct, orderby):
		raise NotImplementedError

	def update(self, table, conditions, values):
		return self.execute(self.update_sql(self.identifier(table), map(self.identifier,values.keys()), self.parse_where(conditions)), values.values())

	def update_sql(self, table, columns, values, conditions):
		raise NotImplementedError


	op_EQUAL = staticmethod(lambda a,b:'%s IS %s'%(a,b))
	op_LESSEQUAL = staticmethod(lambda a,b:'%s<=%s'%(a,b))
	op_GREATERTHAN = staticmethod(lambda a,b:'%s>%s'%(a,b))
	op_NOTEQUAL = staticmethod(lambda a,b:'%s IS NOT %s'%(a,b))
	op_LESSTHAN = staticmethod(lambda a,b:'%s<%s'%(a,b))
	op_GREATEREQUAL = staticmethod(lambda a,b:'%s>=%s'%(a,b))
	op_ADD = staticmethod(lambda a,b:'%s+%s'%(a,b))
	op_CONCATENATE = staticmethod(lambda a,b:'%s||%s'%(a,b))
	op_SUBTRACT = staticmethod(lambda a,b:'%s-%s'%(a,b))
	op_MULTIPLY = staticmethod(lambda a,b:'%s*%s'%(a,b))
	op_DIVIDE = staticmethod(lambda a,b:'%s/%s'%(a,b))
	op_FLOORDIVIDE = staticmethod(lambda a,b:'%s/%s'%(a,b))
	op_MODULO = staticmethod(lambda a,b:'%s%%%s'%(a,b))
	op_AND = staticmethod(lambda a,b:'%s AND %s'%(a,b))
	op_OR = staticmethod(lambda a,b:'%s OR %s'%(a,b))
	op_NOT = staticmethod(lambda a:'NOT %s'%a)
	op_NEGATIVE = staticmethod(lambda a:'-%s'%a)
	op_ABS = staticmethod(lambda a:'abs(%s)'%a)
	op_LENGTH = staticmethod(lambda a:'length(%s)'%a)
	op_ASCEND = staticmethod(lambda a:'%s ASC'%a)
	op_DESCEND = staticmethod(lambda a:'%s DESC'%a)
	op_SUM = staticmethod(lambda a:'total(%s)'%a)
	op_AVERAGE = staticmethod(lambda a:'avg(%s)'%a)
	op_BETWEEN = staticmethod(lambda a,b,c:'%s BETWEEN %s AND %s'%(a,b,c))
	op_MIN = staticmethod(lambda a:'min(%s)'%a)
	op_MAX = staticmethod(lambda a:'max(%s)'%a)
	op_UPPER = staticmethod(lambda a:'upper(%s)'%a)
	op_LOWER = staticmethod(lambda a:'lower(%s)'%a)
	op_LIKE = staticmethod(lambda a,b,c=None:'%s LIKE %s'%(a,b) if c is None else '%s LIKE %s ESCAPE %s'%(a,b,c))
	op_SUBSTRING = staticmethod(lambda a,b,c=None:'substr(%s,%s)'%(a,b) if c is None else 'substr(%s,%s,%s)'%(a,b,c))
	op_GLOB = staticmethod(lambda a,b:'%s GLOB %s' % (a,b))
	op_LSTRIP = staticmethod(lambda a,b=None:'ltrim(%s)'%a if b is None else 'ltrim(%s,%s)'%(a,b))
	op_RSTRIP = staticmethod(lambda a,b=None:'rtrim(%s)'%a if b is None else 'rtrim(%s,%s)'%(a,b))
	op_STRIP = staticmethod(lambda a,b=None:'trim(%s)'%a if b is None else 'trim(%s,%s)'%(a,b))
	op_REPLACE = staticmethod(lambda a,b,c:'replace(%s,%s,%s)'%(a,b,c))
	op_ROUND = staticmethod(lambda a,b=None:'round(%s)'%a if b is None else 'round(%s,%s'%(a,b))
	op_COALESCE = staticmethod(lambda a,b,*c:'coalesce(%s)'%(','.join((a,b)+c)))
