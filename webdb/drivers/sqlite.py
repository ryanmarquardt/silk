
from .base import *

import sqlite3
import errno

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
	
	OperationalError = sqlite3.OperationalError
	
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
		ABS:lambda a:'abs(%s)'%a,
		LENGTH:lambda a:'length(%s)'%a,
		ASCEND:lambda a:'%s ASC'%a,
		DESCEND:lambda a:'%s DESC'%a,
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
