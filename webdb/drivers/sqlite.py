
from webdoc import container
import sqlite3

class sqlite(object):
	def __init__(self, path=':memory:'):
		self.path = path
		self.connection = sqlite3.connect(path)
		self.depth = 0
		
	def __enter__(self):
		self.depth += 1
		return self.connection.cursor()
		
	def __exit__(self, obj, exc, tb):
		self.depth -= 1
		if self.depth == 0:
			if obj:
				self.connection.rollback()
			else:
				self.connection.commit()
		
	def list_tables(self):
		with self as cursor:
			return (n for (n,) in self.execute("""SELECT name FROM sqlite_master WHERE type='table'"""))
		
	def list_columns(self, table):
		with self as cursor:
			return sorted((idx,str(name),str(v_type),bool(notnull),default) for (idx,name,v_type,notnull,default,_) in self.execute("""PRAGMA table_info("%s");""" % table))
			
	@staticmethod
	def format_value(val):
		if val is None:
			return 'NULL'
		else:
			return str(val)

	@classmethod
	def format_column(cls, field):
		props = container(vars(field))
		props.notnull = 'NOT NULL' if field.notnull else ''
		props.default = 'DEFAULT %s'%cls.format_value(field.default) if field.notnull or not field.default is None else ''
		return '%(name)s %(type)s %(notnull)s %(default)s' % props

	def create_table_if_nexists(self, name, table):
		with self as cursor:
			self.execute("""CREATE TABLE IF NOT EXISTS %s(%s);""" % (
				name,
				', '.join(map(self.format_column,table.fields()))
			))

	def execute(self, sql, values=()):
		with self as cursor:
			return cursor.execute(sql, values)
		
