
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
	def __init__(self, path=':memory:', debug=False):
		self.path = path
		try:
			driver_base.__init__(self, sqlite3.connect(path, sqlite3.PARSE_DECLTYPES), debug)
		except sqlite3.OperationalError, e:
			if e.message == 'unable to open database file':
				e = IOError(errno.ENOENT, 'No such file or directory: %r' % path)
				e.errno = errno.ENOENT
			raise e
	
	webdb_types = {
		'rowid':'INTEGER PRIMARY KEY',
		'string':'TEXT',
		'integer':'INT',
		'float':'REAL',
		'data':'BLOB',
		'boolean':'INT',
		'datetime':'TIMESTAMP',
		'reference':'REFERENCES %(table)s(%(column)s)',
	}
	
	driver_types = {
		'TEXT':'string',
		'INT':'integer',
		'INTEGER':'rowid',
		'REAL':'float',
		'BLOB':'data',
		'TIMESTAMP':'datetime',
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
			

	def create_table_if_nexists_sql(self, name, *coldefs):
		return """CREATE TABLE IF NOT EXISTS %s(%s);""" % (name, ', '.join(coldefs))

	def create_table_sql(self, name, *coldefs):
		return """CREATE TABLE %s(%s);""" % (name, ', '.join(coldefs))

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
			' ORDER BY %s'%', '.join(self.expression(o).strip('()') for o in orderby) if orderby else '',
		)

	def insert_sql(self, table, names):
		return """INSERT INTO %s(%s) VALUES (%s)""" % (table, ','.join(names), ','.join(list('?'*len(names))))

	def update_sql(self, table, names, where):
		return """UPDATE %s SET %s%s;""" % (table, ', '.join('%s=?'%n for n in names), where)

	def delete_sql(self, table, where):
		return """DELETE FROM %s%s;""" % (table, where)
