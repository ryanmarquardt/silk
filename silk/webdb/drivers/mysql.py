
from .base import *

import warnings

import MySQLdb

class mysql(driver_base):
	"""Driver for mysql databases

	mysql requires only one parameter: database, which is the name of the
	database to use.

	>>> mydb = DB.connect('mysql', 'silk_test', user='silk_test', engine='InnoDB')
	"""
	test_args = ('silk_test','silk_test')
	test_kwargs = {'engine':'InnoDB'}

	engines = {'MyISAM','InnoDB','MERGE','MEMORY','BDB','EXAMPLE','FEDERATED','ARCHIVE','CSV','BLACKHOLE'}

	id_quote = '`'

	def __init__(self, database, user='root', password=None, host='localhost', engine='MyISAM', debug=False):
		self.database = database
		self.user = user
		self.password = password
		self.__db_api_init__(MySQLdb, host=host, user=user, passwd=password or '', db=database, debug=debug)
		self.engine = engine

	@property
	def engine(self):
		return self.__dict__['engine']
	@engine.setter
	def engine(self, new):
		assert new in self.engines, 'Unknown storage engine %r' % new
		if new in {'InnoDB', 'BDB'}:
			self.features.add('transactions')
		else:
			self.features.discard('transactions')
		self.__dict__['engine'] = new

	webdb_types = {
		int:'INT',
		float:'REAL',
		bool:'TINYINT(1)',
		unicode:'VARCHAR(512)',
		bytes:'BLOB',
		datetime.datetime:'DATETIME',
	}

	def handle_exception(self, e):
		if isinstance(e, MySQLdb.OperationalError):
			code = e.args[0]
			if code in (1044, 1049):
				raise make_IOError('ENOENT', 'No such database: %r' % self.database)
			elif code == 1045:
				raise AuthenticationError(self.user)
			elif code == 1054:
				raise KeyError(e.args[1])
		elif isinstance(e, MySQLdb.IntegrityError):
			code = e.args[0]
			if code == 1062:
				raise ValueError(e.message)
		elif isinstance(e, MySQLdb.ProgrammingError):
			text = e.args[1].partition("'")[2].rpartition("'")[0]
			offset = self.lastsql.index(text)
			raise SQLSyntaxError(self.lastsql, offset, text)


	def unmap_type(self, t):
		name, _, size = t.partition('(')
		if name in ('int','tinyint'):
			return int if int((size or '0 ')[:-1]) > 1 else bool
		return {'text':unicode, 'varchar':unicode,
			'timestamp':datetime.datetime, 'double':float, 'real':float,
			'blob':bytes}.get(name)
	
	def list_tables_sql(self):
		return """SHOW TABLES;"""
		
	def list_columns(self, table):
		for name,v_type,null,key,default,extra in self.execute("""DESCRIBE %s;""" % table):
			ut = self.unmap_type(v_type)
			if not ut:
				raise Exception('Unknown column type %s' % v_type)
			yield (str(name),ut,null!='YES',default)

	def create_table_if_nexists(self, name, columns, primarykeys):
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			return self.execute("""CREATE%s TABLE IF NOT EXISTS %s(%s%s) ENGINE=%s;""" % (
				' TEMPORARY' if self.debug else '',
				name,
				', '.join(columns),
				(', PRIMARY KEY (%s)' % ', '.join('%s ASC'%p for p in primarykeys)) if primarykeys else '',
				self.engine
			))

	def insert_rowid(self, cursor):
		return self.connection.insert_id()

	op_SUM = staticmethod(lambda a:'sum(%s)'%a)
	op_CONCATENATE = staticmethod(lambda a,b:'CONCAT(%s,%s)'%(a,b))
