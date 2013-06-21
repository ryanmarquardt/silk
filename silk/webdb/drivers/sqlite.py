
from .base import *

import sqlite3
import errno

class sqlite(driver_base):
	"""Driver for sqlite3 databases

	sqlite accepts only one parameter: path, which is the path of the database
	file. By default, path=':memory:', which creates a temporary database
	in memory.
	"""
	test_args = ()
	
	param_marker = '?'
	
	def __init__(self, path=':memory:', debug=False):
		self.path = path
		try:
			driver_base.__init__(self, sqlite3.connect(path, sqlite3.PARSE_DECLTYPES), debug)
		except sqlite3.OperationalError, e:
			if e.message == 'unable to open database file':
				e = IOError(errno.ENOENT, 'No such file or directory: %r' % path)
				e.errno = errno.ENOENT
			raise e

	def normalize_column(self, column):
		r = driver_base.normalize_column(self, column)
		if r.primarykey:
			r.autoinc_sql = ''
		return r

	webdb_types = {
		int:'INTEGER',
		float:'REAL',
		bool:'INT',
		unicode:'TEXT',
		bytes:'BLOB',
		datetime.datetime:'TIMESTAMP',
	}
	
	driver_types = {
		'TEXT':unicode,
		'INTEGER':int,
		'REAL':float,
		'BLOB':bytes,
		'TIMESTAMP':datetime.datetime,
	}

	def handle_exception(self, e):
		if isinstance(e, sqlite3.OperationalError):
			msg = e.args[0]
			if 'has no column named' in msg or msg.startswith('no such column: '):
				raise KeyError("No such column in table: %s" % msg.rsplit(None, 1)[1])

	def list_tables_sql(self):
		return """SELECT name FROM sqlite_master WHERE type='table'"""

	def list_columns(self, table):
		for _,name,v_type,notnull,default,_ in self.execute("""PRAGMA table_info("%s");""" % table):
			yield (str(name),self.unmap_type(v_type),bool(notnull),default)

	def create_table_if_nexists_sql(self, name, coldefs, primarykeys):
		if primarykeys:
			return """CREATE TABLE IF NOT EXISTS %s(%s, PRIMARY KEY (%s));""" % (name, ', '.join(coldefs), ', '.join('%s ASC'%p for p in primarykeys))
		else:
			return """CREATE TABLE IF NOT EXISTS %s(%s);""" % (name, ', '.join(coldefs))

	def rename_table_sql(self, orig, new):
		return """ALTER TABLE %s RENAME TO %s;""" % (orig, new)

	def add_column_sql(self, table, column):
		return """ALTER TABLE %s ADD COLUMN %s;""" % (table, column)

	def drop_table_sql(self, table):
		return """DROP TABLE %s;""" % (table)

	def select_sql(self, columns, tables, where, distinct, orderby):
		return """SELECT%s %s FROM %s%s%s;""" % (
			' DISTINCT' if distinct else '',
			', '.join(columns),
			', '.join(tables),
			where,
			' ORDER BY %s'%', '.join(orderby) if orderby else '',
		)

	def insert_sql(self, table, columns, values):
		return """INSERT INTO %s(%s) VALUES (%s)""" % (table, ','.join(columns), ','.join(values))

	def update_sql(self, table, columns, values, where):
		return """UPDATE %s SET %s%s;""" % (table, ', '.join('%s=%s'%i for i in zip(columns,values)), where)

	def delete_sql(self, table, where):
		return """DELETE FROM %s%s;""" % (table, where)
