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
class LENGTH(op): pass
LENGTH = LENGTH()

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
		return '%(name)s %(type)s%(notnull)s%(default)s' % {
			'name': self.identifier(column.name),
			'type': self.map_type(column.type),
			'notnull': ' NOT NULL' if column.notnull else '',
			'default': " DEFAULT %s"%self.literal(column.default, props.type) if column.notnull or not column.default is None else ''
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
		return self.execute(self.select_sql(map(self.expression,columns), [self.identifier(t._name) for t in tables], self.parse_where(conditions)))

	def insert(self, table, values):
		cur = self.execute(self.insert_sql(self.identifier(table), map(self.identifier,values.keys())), values.values())
		return cur.lastrowid

	def update(self, table, conditions, values):
		return self.execute(self.update_sql(self.identifier(table), map(self.identifier,values.keys()), self.parse_where(conditions)), values.values())

	def delete(self, table, conditions):
		return self.execute(self.delete_sql(self.identifier(table), self.parse_where(conditions)))


