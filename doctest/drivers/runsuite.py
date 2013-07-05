#!/usr/bin/env python

import ConfigParser
import os
import unittest

from silk.webdb import *
import silk.webdb.drivers

class DriverTestBase(unittest.TestCase):
	def setUp(self):
		self.connect()

	def connect(self, **kwargs):
		new = dict(filter(lambda (k,v):not k.startswith('_'), self.options.items()))
		new.update(kwargs)
		self.db = DB.connect(self.driver, **new)

class DriverTestConnection(DriverTestBase):
	#def run_driver(self, section):
		#options = dict(filter(lambda (k,v):not k.startswith('_'), conf.items(driver)))
		#options.update(dict(filter(lambda (k,v):not k.startswith('_'), conf.items(section))))
		#options['debug'] = True
		#exc = eval(conf.get(section, '__raises__') if conf.has_option(section, '__raises__') else 'Exception')
		#with self.assertRaises(exc):
			#DB.connect(self.driver, **options)

	#def test_drivers(self):
		#sections = filter(lambda name:name.startswith(args.driver+':'), conf.sections())
		#for section in sections:
			#self.run_driver(section)

	def test_invalid_driver_name(self):
		with self.assertRaises(UnknownDriver):
			DB.connect('<>invalid name+/%')

	def test_driver_base(self):
		with self.assertRaises(UnknownDriver):
			DB.connect('base')

class DriverTestTableCreation(DriverTestBase):
	def test_create_no_explicit_columns(self):
		self.db.define_table('rowid_only')
		self.assertEqual(len(self.db.rowid_only._columns), 1)

	def test_create_no_columns(self):
		with self.assertRaises(RuntimeError):
			self.db.define_table('no_columns', primarykey=[])

	def test_bad_column_name(self):
		with self.assertRaises(NameError):
			self.db.define_table('table1', StrColumn('bad identifier'))

	def test_create_strcolumn(self):
		self.db.define_table('table1', StrColumn('data'))
		self.assertIn('table1', self.db)

	def test_create_duplicate(self):
		self.db.define_table('table1')
		with self.assertRaisesRegexp(AttributeError, ' already defined'):
			self.db.define_table('table1')

class DriverTestInsert(DriverTestBase):
	def setUp(self):
		DriverTestBase.setUp(self)

	def table1(self):
		self.db.define_table('table1', StrColumn('data'))

	def messages(self):
		self.db.define_table('messages',
			ReferenceColumn('owner', db.users),
			StrColumn('subject'),
			StrColumn('content'),
			DateTimeColumn('sent', default=datetime.datetime.now),
		)
		self.assertIn('messages', self.db)

	def test_cloning(self):
		self.table1()
		self.db.define_table('table2', self.db.table1)
		self.assertIsNot(self.db.table1, self.db.table2)
		self.assertEqual(self.db.table1, self.db.table2)
		self.assertEqual(self.db.table1._name, 'table1')
		self.assertEqual(self.db.table2._name, 'table2')
		self.assertIsNot(self.db.table1.data, self.db.table2.data)

	def test_good_reference(self):
		self.table1()
		self.db.define_table('table2', ReferenceColumn('ref', self.db.table1))

	def test_bad_reference(self):
		self.db.define_table('table1', StrColumn('data'), primarykey=[])
		with self.assertRaises(TypeError):
			self.db.define_table('table2', ReferenceColumn('badref', self.db.table1))

	def test_insert(self):
		self.table1()
		self.db.table1.insert(data='12345')
		with self.assertRaises(KeyError):
			self.db.table1.insert(nonexistent=True)
		self.db.table1.insert(data=23456)
		data = [row.data for row in self.db.table1.select()]
		self.assertSequenceEqual(data, [u'12345', u'23456'])
		self.assertEqual(len(self.db.table1), 2)

	def test_string_coersion(self):
		self.db.define_table('table1', StrColumn('data', unique=True))
		self.db.table1.insert(data='12345')
		with self.assertRaises(ValueError):
			self.db.table1.insert(data=12345)
		with self.assertRaises(ValueError):
			self.db.table1.insert(data=u'12345')

	def test_integer_coersion(self):
		self.db.define_table('table1', IntColumn('data', unique=True))
		self.db.table1.insert(data=12345)
		with self.assertRaises(ValueError):
			self.db.table1.insert(data=12345.0)
		with self.assertRaises(ValueError):
			self.db.table1.insert(data='12345')

	def test_column_name_clash(self):
		"It is awkward, but possible to name columns after methods of Table"
		self.db.define_table('table1', StrColumn('insert'))
		self.assertIn('table1', self.db)
		self.assertNotIsInstance(self.db.table1.insert, Column)
		self.db.table1.insert(insert='1')
		self.assertEqual(len(self.db.table1._columns['insert'] == '1'), 1)

	def test_no_primarykey(self):
		self.db.define_table('table1', StrColumn('data'), primarykey=[])
		self.db.table1.insert(data='abc')
		with self.assertRaises(TypeError):
			self.db.table1[1]
		self.assertEqual((self.db.table1.data=='abc').select().one().primarykey, ())

class DriverTestSelect(DriverTestBase):
	def setUp(self):
		DriverTestBase.setUp(self)
		self.db.define_table('users',
			StrColumn('first_name'),
			StrColumn('last_name'),
			StrColumn('email'),
			IntColumn('age', default=18),
			DateTimeColumn('registered', default=datetime.datetime.now),
			primarykey = 'email',
		)
		self.assertIn('users', self.db)
		self.db.users.insert_many(
			{'first_name':'Maggie','last_name':'Reynolds','email':'magginator@email.com','registered':datetime.datetime(2012,5,5)},
			{'first_name':'Bob','last_name':'Smith','email':'bob.smith@email.com','age':23,'registered':datetime.datetime(2010,4,12)},
			{'first_name':'Pat','last_name':'Smith','email':'pat.smith@email.com','age':19,'registered':datetime.datetime(2010,4,12)},
			{'first_name':'Werfina','last_name':'Fablesmok','email':'wgf@email.com','age':'45','registered':datetime.datetime(2012,5,6)},
		)

	def test_select_all(self):
		self.assertItemsEqual(map(tuple,self.db.users.select()), [
			(u'Maggie', u'Reynolds', u'magginator@email.com', 18, datetime.datetime(2012, 5, 5, 0, 0)),
			(u'Bob', u'Smith', u'bob.smith@email.com', 23, datetime.datetime(2010, 4, 12, 0, 0)),
			(u'Pat', u'Smith', u'pat.smith@email.com', 19, datetime.datetime(2010, 4, 12, 0, 0)),
			(u'Werfina', u'Fablesmok', u'wgf@email.com', 45, datetime.datetime(2012, 5, 6, 0, 0)),
		])

	def test_select_args(self):
		self.assertItemsEqual(map(tuple,self.db.users.select(self.db.users.first_name, self.db.users.last_name, orderby=self.db.users.last_name)), [
			(u'Maggie', u'Reynolds'),
			(u'Bob', u'Smith'),
			(u'Pat', u'Smith'),
			(u'Werfina', u'Fablesmok'),
		])

	def test_select_complex_orderby(self):
		self.assertEqual(map(tuple,self.db.users.select(
			self.db.users.first_name,
			self.db.users.last_name,
			orderby=[
				self.db.users.last_name,
				reversed(self.db.users.first_name)
			])), [
			(u'Werfina', u'Fablesmok'),
			(u'Maggie', u'Reynolds'),
			(u'Pat', u'Smith'),
			(u'Bob', u'Smith'),
		])

	def test_select_where(self):
		self.assertItemsEqual(map(tuple,(self.db.users.age > 20).select()), [
			(u'Bob', u'Smith', u'bob.smith@email.com', 23, datetime.datetime(2010, 4, 12, 0, 0)),
			(u'Werfina', u'Fablesmok', u'wgf@email.com', 45, datetime.datetime(2012, 5, 6, 0, 0)),
		])

	def test_select_distinct(self):
		self.assertEqual(map(vars, self.db.users.select(self.db.users.last_name, distinct=True, orderby=self.db.users.last_name)),
		[dict(last_name=u'Fablesmok'), dict(last_name=u'Reynolds'), dict(last_name=u'Smith')])

	def test_select_aggregate(self):
		self.assertEqual(self.db.users.select(self.db.users.age.sum()).one()[0], 105)
		self.assertEqual(self.db.users.get(self.db.users.age.sum()), 105)
		self.assertEqual(self.db.users.select(self.db.users.age.average()).one()[0], 26.25)
		self.assertEqual(self.db.users.select(self.db.users.age.max()).one()[0], 45)

	def test_select_complex_comparison(self):
		self.assertItemsEqual(map(tuple, self.db.users.age.between(19,30).select()), [
			(u'Bob', u'Smith', u'bob.smith@email.com', 23, datetime.datetime(2010, 4, 12, 0, 0)),
			(u'Pat', u'Smith', u'pat.smith@email.com', 19, datetime.datetime(2010, 4, 12, 0, 0)),
		])

	def test_record_update(self):
		record = self.db.users['magginator@email.com']
		self.assertEqual(record.age, 18)
		self.assertEqual(record.update(age=record.age+1).age, 19)
		self.assertEqual(self.db.users['magginator@email.com'].age, 19)

	def test_record_bad_update(self):
		record = self.db.users['magginator@email.com']
		with self.assertRaises(KeyError):
			record.update(nonexistent=True)
		with self.assertRaises(NameError):
			record.update(**{'bad identifier':True})

	def test_no_such_record(self):
		with self.assertRaises(KeyError):
			self.db.users['not.in.db@email.com']

	def test_select_substring(self):
		self.assertEqual([r[0] for r in self.db.users.select(self.db.users.last_name[0], orderby=self.db.users.email)],
			[u'S', u'R', u'S', u'F'])
		self.assertEqual([r[0] for r in self.db.users.select(self.db.users.last_name[3:5], orderby=self.db.users.email)],
			[u'th', u'no', u'th', u'le'])
		self.assertEqual([r[0] for r in self.db.users.select(self.db.users.last_name[1:], orderby=self.db.users.email)],
			[u'mith', u'eynolds', u'mith', u'ablesmok'])
		self.assertEqual([r[0] for r in self.db.users.select(self.db.users.last_name[-1:], orderby=self.db.users.email)],
			[u'h', u's', u'h', u'k'])
		self.assertEqual([r[0] for r in self.db.users.select(self.db.users.last_name[:-1], orderby=self.db.users.email)],
			[u'Smit', u'Reynold', u'Smit', u'Fablesmo'])
		self.assertEqual([r[0] for r in self.db.users.select(self.db.users.age[1:], orderby=self.db.users.email)],
			[3, 8, 9, 5])

	def test_select_combined(self):
		self.assertItemsEqual([r[0] for r in self.db.users.select(self.db.users.first_name + ' ' + self.db.users.last_name)],
			[u'Pat Smith', u'Maggie Reynolds', u'Bob Smith', u'Werfina Fablesmok'])

	def test_null_comparison(self):
		self.assertEqual(len(self.db.users.last_name != 'Smith'), 2)
		self.assertEqual(len(self.db.users.last_name != None), 4)

	def test_select_aggregate_column(self):
		self.assertEqual([row.last_name for row in self.db.users.last_name.startswith('S').select()],
			[u'Smith', u'Smith'])
		self.assertEqual([row.last_name for row in self.db.users.last_name.endswith('s').select()],
			[u'Reynolds'])

	def test_selection_iteration(self):
		self.db.define_table('table1', StrColumn('data'))
		self.db.table1.insert(data='a')
		selection = self.db.table1.select()
		count = 0
		for row in selection:
			count += 1
		self.assertEqual(count, 1)
		for row in selection:
			count += 1
		self.assertEqual(count, 1)

	def test_selection_truth_value(self):
		self.db.define_table('table1', StrColumn('data'), IntColumn('value'))
		self.db.table1.insert(data='a', value=1)
		self.db.table1.insert(data='b', value=2)
		selection = (self.db.table1.data == 'a').select()
		 #__nonzero__ must fetch a row, but it stores it for later use
		self.assertTrue(selection)
		self.assertEqual(map(tuple,selection), [(u'a', 1)])
		self.assertEqual(map(tuple,selection), [])
		#Non-zero tests are consistent as long as data remains in the cursor
		selection = (self.db.table1.data != None).select()
		count = 0
		while selection:
			row = selection.next()
			count += 1
			self.assertIn(row.data, (u'a', u'b'))
			self.assertIn(row.value, (1, 2))
			self.assertEqual({u'a':1, u'b':2}[row.data], row.value)
		self.assertEqual(count, 2)
		self.assertFalse((self.db.table1.data == '').select())

	def test_select_first_last(self):
		self.db.define_table('test', StrColumn('data'))
		for x in map(unicode, range(10)):
			self.db.test.insert(data=x)
		selection = self.db.test.select(orderby=self.db.test.data)
		self.assertEqual(selection.first(), '0')
		self.assertEqual(selection.first(), '1')
		selection.skip(2)
		self.assertEqual(selection.one(), '4')
		self.assertEqual(selection.last(), '9')
		self.assertEqual(selection.last(), None)
		self.assertEqual(selection.first(), None)

	def test_select_slice(self):
		self.db.define_table('test', StrColumn('data'))
		for x in map(unicode, range(10)):
			self.db.test.insert(data=x)
		selection = self.db.test.select(orderby=self.db.test.data)
		self.assertEqual(len(selection[4:]), 6)
		selection = self.db.test.select(orderby=self.db.test.data)
		self.assertEqual(map(tuple,selection[:]), map(tuple,map(unicode,range(10))))

class DriverTestReferences(DriverTestBase):
	def setUp(self):
		DriverTestBase.setUp(self)
		self.db.define_table('addresses',
			StrColumn('name', primarykey=True),
			StrColumn('domain', primarykey=True),
			BoolColumn('active', default=False))
		self.db.define_table('accounts',
			ReferenceColumn('address', self.db.addresses, lambda row:row.name+'@'+row.domain),
			StrColumn('owner_name'))
		self.db.addresses.insert_many(
			dict(name='webmaster', domain='example.com', active=True),
			dict(name='postmaster', domain='example.com', active=True),
			dict(name='cerealmaster', domain='example.com'))
		self.db.accounts.insert(address=self.db.addresses['webmaster', 'example.com'], owner_name='The Webmaster')

	def test_cross_select(self):
		wm = self.db.addresses['webmaster', 'example.com']
		self.assertEquals(tuple(wm.accounts.select().one()), (u'webmaster@example.com', 'The Webmaster'))

class DriverTestExceptions(DriverTestBase):
	def test_sqlsyntaxerror(self):
		self.db.__driver__.op_AND = lambda a,b:'%s AD %s'%(a,b)
		self.db.define_table('test', StrColumn('a'), StrColumn('b'))
		with self.assertRaises(silk.webdb.SQLSyntaxError):
			((self.db.test.a == None) & (self.db.test.b == None)).select()


def main(driver):
	import argparse
	import sys

	parser = argparse.ArgumentParser()
	parser.add_argument('-v', dest='verbosity', nargs='?', action='store', type=int, default=1)
	args = parser.parse_args()
	
	DriverTestBase.driver = driver
	
	conf = ConfigParser.ConfigParser()
	x = ['drivers.conf']
	f = os.path.abspath(__file__)
	while f != '/':
		f = os.path.split(f)[0]
		x.append(os.path.join(f,'drivers.conf'))
	conf.read(x)

	DriverTestBase.options = dict(conf.items(driver))
	DriverTestBase.options['debug'] = True

	unittest.main(verbosity=args.verbosity, argv=sys.argv[:1])
