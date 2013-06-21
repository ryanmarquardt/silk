
from .base import *

import sqlite3
import errno

class sqlite(driver_base):
	"""Driver for sqlite3 databases

	sqlite accepts only one parameter: path, which is the path of the database
	file. By default, path=':memory:', which creates a temporary database
	in memory.
	"""
	parameters = driver_base.parameters_qmark
	id_quote = '"'
	
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
		for _,name,v_type,notnull,default,_ in self.execute("""PRAGMA table_info(%s);""" % table):
			yield (str(name),self.unmap_type(v_type),bool(notnull),default)

	def create_table_if_nexists_sql(self, name, coldefs, primarykeys):
		if primarykeys:
			return """CREATE TABLE IF NOT EXISTS %s(%s, PRIMARY KEY (%s));""" % (name, ', '.join(coldefs), ', '.join('%s ASC'%p for p in primarykeys))
		else:
			return """CREATE TABLE IF NOT EXISTS %s(%s);""" % (name, ', '.join(coldefs))

	def _drop_column(self, table, column):
		raise NotImplementedError
