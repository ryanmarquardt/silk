
from .base import *

import MySQLdb
import errno

class mysql(driver_base):
	"""Driver for mysql databases

	mysql requires only one parameter: database, which is the name of the
	database to use. 
	"""
	test_args = ('silk_test','silk_test')
	def __init__(self, database, user='root', password=None, host='localhost', debug=False):
		self.database = database
		self.host = host
		self.user = user
		self.password = password
		try:
			driver_base.__init__(self, MySQLdb.connect(host=host, user=user, passwd=password or '', db=database), debug)
		except MySQLdb.OperationalError, e:
			raise e
	
	webdb_types = {
		'rowid':'INTEGER AUTO_INCREMENT PRIMARY KEY',
		'string':'VARCHAR(512)',
		'integer':'INT',
		'float':'REAL',
		'data':'BLOB',
		'boolean':'TINYINT(1)',
		'datetime':'TIMESTAMP',
		'reference':'REFERENCES %(table)s(%(column)s)',
	}
	
	driver_types = {
		'TEXT':'string',
		'INT':'integer',
		'REAL':'float',
		'BLOB':'data',
		'TIMESTAMP':'datetime',
	}
	
	def handle_exception(self, e):
		if isinstance(e, MySQLdb.OperationalError):
			raise e
			#msg = e.args[0]
			#if 'has no column named' in msg or msg.startswith('no such column: '):
				#raise KeyError("No such column in table: %s" % msg.rsplit(None, 1)[1])

	def identifier(self, name):
		if not name.replace('_','').isalnum():
			raise NameError("Column names can only contain letters, numbers, and underscores. Got %r" % name)
		return '`%s`'%name

	def unmap_type(self, t):
		name, y, size = t.partition('(')
		if y:
			size = int(size[:-1])
		if name in ('int','tinyint'):
			return 'integer' if size > 1 else 'boolean'
		elif name in ('text','varchar'):
			return 'string'
		elif name == 'timestamp':
			return 'datetime'
		elif name in ('double','real'):
			return 'float'
		elif name in ('blob',):
			return 'data'
	
	def list_tables_sql(self):
		return """SHOW TABLES;"""
		
	def list_columns(self, table):
		for name,v_type,null,key,default,extra in self.execute("""DESCRIBE %s;""" % table):
			ut = self.unmap_type(v_type)
			if not ut:
				raise Exception('Unknown column type %s' % v_type)
			yield (str(name),ut,null!='YES',default)
			

	def create_table_if_nexists_sql(self, name, *coldefs):
		if self.debug:
			return """CREATE TEMPORARY TABLE IF NOT EXISTS %s(%s);""" % (name, ', '.join(coldefs))
		else:
			return """CREATE TABLE IF NOT EXISTS %s(%s);""" % (name, ', '.join(coldefs))

	def create_table_sql(self, name, *coldefs):
		if self.debug:
			return """CREATE TEMPORARY TABLE %s(%s);""" % (name, ', '.join(coldefs))
		else:
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

	def insert(self, table, values):
		cur = self.execute(self.insert_sql(self.identifier(table), map(self.identifier,values.keys())), values.values())
		return self.connection.insert_id()

	def insert_sql(self, table, names):
		return """INSERT INTO %s(%s) VALUES (%s)""" % (table, ','.join(names), ','.join(['%s']*len(names)))

	def update_sql(self, table, names, where):
		return """UPDATE %s SET %s%s;""" % (table, ', '.join('%s=%%s'%n for n in names), where)

	def delete_sql(self, table, where):
		return """DELETE FROM %s%s;""" % (table, where)
