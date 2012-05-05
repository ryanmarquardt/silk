
from webdoc import container
import sqlite3

class driver_base(object):
	def create_table_if_nexists(self, name, table):
		if name not in self.list_tables:
			self.create_table(name, table)

class sqlite(object):
	"""Driver for sqlite3 databases

	sqlite accepts only one parameter: path, which is the path of the database
	file. By default, path=':memory:', which creates a temporary database
	in memory.
	"""
	def __init__(self, path=':memory:'):
		self.path = path
		self.connection = sqlite3.connect(path)
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
		with self as cursor:
			return cursor.execute(sql, values)
		
	def list_tables(self):
		return (str(n) for (n,) in self.execute("""SELECT name FROM sqlite_master WHERE type='table'"""))
		
	def list_columns(self, table):
		return ((str(name),str(v_type),bool(notnull),default) for (_,name,v_type,notnull,default,_) in self.execute("""PRAGMA table_info("%s");""" % table))
			
	@staticmethod
	def format_value(val):
		if val is None:
			return 'NULL'
		else:
			return str(val)

	@classmethod
	def format_column(cls, column):
		props = container(vars(column))
		props.notnull = 'NOT NULL' if column.notnull else ''
		props.default = "DEFAULT '%s'"%cls.format_value(column.default) if column.notnull or not column.default is None else ''
		return '%(name)s %(type)s %(notnull)s %(default)s' % props

	def create_table_if_nexists(self, name, table):
		self.execute("""CREATE TABLE IF NOT EXISTS %s(%s);""" % (
			name,
			', '.join(map(self.format_column, table))
		))

	def create_table(self, name, table):
		self.execute("""CREATE TABLE %s(%s);""" % (
			name,
			', '.join(map(self.format_column,table))
		))

	def rename_table(self, orig, new):
		self.execute("""ALTER TABLE %s RENAME TO %s;""" % (orig, new))

	def alter_table(self, name, table):
		with self:
			db_cols = self.list_columns(name)
			db_names = [c[0] for c in db_cols]
			for column in table:
				if column.name not in db_names:
					self.execute("""ALTER TABLE %s ADD COLUMN %s;"""%(
						name, self.format_column(column)
					))

	def select(self, columns, table, conditions):
		return self.execute("""SELECT %s FROM %s WHERE %s""" % (
			', '.join(['rowid'] + columns),
			table,
			' and '.join("%s=%s"%i for i in conditions),
		)).fetchall()

	def insert(self, values, table):
		cur = self.execute("""INSERT INTO %s(%s) VALUES (%s)""" % (
			table,
			','.join(values.keys()),
			','.join(list('?'*len(values))),
		), values.values())
		return cur.lastrowid
