
from webdoc import sequence

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
	
	  * operators: a dictionary mapping operator objects (EQUAL, MULTIPLY, etc.)
	      to functions that format those operations. See drivers/sqlite.py
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
			return '(%s)'%self.operators[operator](*map(self.expression,x[1:]))
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
		type = self.map_type(column.type)
		#if not callable(column.default)
		default = " DEFAULT %s"%self.literal(column.default, self.map_type(column.type)) if not callable(column.default) and (column.notnull or not column.default is None) else ''
		return '%(name)s %(type)s%(notnull)s%(default)s' % {
			'name': self.identifier(column.name),
			'type': type,
			'notnull': ' NOT NULL' if column.notnull else '',
			'default': default
		}

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


	def create_table_if_nexists_sql(self, name, *columns):
		'''create_table_if_nexists_sql(self, name, *columns) -> Stub
		
		Base classes should return SQL for creating a table if it doesn't
		exist. '''
		raise NotImplementedError

	def create_table_if_nexists(self, name, table):
		if hasattr(self, 'create_table_if_nexists_sql'):
			self.execute(self.create_table_if_nexists_sql(
				self.identifier(name),
				*map(self.format_column, table.columns)
			))
		elif name not in self.list_tables:
			self.create_table(name, table.columns)

	def create_table_sql(self, name, *columns):
		raise NotImplementedError

	def create_table(self, name, table):
		try:
			self.execute(self.create_table_sql(self.identifier(name), *map(self.format_column,table.columns)))
		except NotImplementedError:
			self.create_table_if_nexists(name, table.columns)

	def list_tables(self):
		return (str(n) for (n,) in self.execute(self.list_tables_sql()))

	def rename_table(self, orig, new):
		self.execute(self.rename_table_sql(self.identifier(orig), self.identifier(new)))

	def alter_table(self, name, table):
		with self:
			db_cols = self.list_columns(name)
			db_names = [c[0] for c in db_cols]
			for column in table.columns:
				if column.name not in db_names:
					self.execute(self.add_column_sql(self.identifier(name), self.format_column(column)))

	def select(self, columns, tables, conditions, props):
		return self.execute(self.select_sql(
			([self.identifier('rowid')]if len(tables)==1 and not props.get('distinct') else [])+map(self.expression,columns),
			[self.identifier(t._name) for t in tables],
			self.parse_where(conditions),
			props.get('distinct',False),
			sequence(props.get('orderby',[])),
		))

	def insert(self, table, values):
		cur = self.execute(self.insert_sql(self.identifier(table), map(self.identifier,values.keys())), values.values())
		return cur.lastrowid

	def update(self, table, conditions, values):
		return self.execute(self.update_sql(self.identifier(table), map(self.identifier,values.keys()), self.parse_where(conditions)), values.values())

	def delete(self, table, conditions):
		return self.execute(self.delete_sql(self.identifier(table), self.parse_where(conditions)))


