#!/usr/bin/env python

import argparse
import ConfigParser
import inspect
import os
import unittest

from silk.webdb import *
import silk.webdb.drivers

parser = argparse.ArgumentParser()
parser.add_argument('driver', nargs='?', default='<all>')
args = parser.parse_args()

import sys

sys.argv = sys.argv[:1]

if args.driver == '<all>':
	import subprocess
	for driver in silk.webdb.drivers.__all__:
		subprocess.Popen(['python', __file__, driver]).communicate()
	exit(0)

conf = ConfigParser.ConfigParser()
x = ['drivers.conf']
f = os.path.abspath(__file__)
while f != '/':
	f = os.path.split(f)[0]
	x.append(os.path.join(f,'drivers.conf'))
conf.read(x)

class DriverTestBase(unittest.TestCase):
	def setUp(self):
		self.driver = args.driver
		self.options = dict(filter(lambda (k,v):not k.startswith('_'), conf.items(self.driver)))
		self.options['debug'] = True
		self.db = DB.connect(self.driver, **self.options)

class DriverTestConnection(DriverTestBase):
	def setUp(self):
		self.driver = args.driver

	def run_driver(self, section):
		options = dict(filter(lambda (k,v):not k.startswith('_'), conf.items(self.driver)))
		options.update(dict(filter(lambda (k,v):not k.startswith('_'), conf.items(section))))
		options['debug'] = True
		exc = eval(conf.get(section, '__raises__') if conf.has_option(section, '__raises__') else 'Exception')
		with self.assertRaises(exc):
			DB.connect(self.driver, **options)

	def test_drivers(self):
		sections = filter(lambda name:name.startswith(args.driver+':'), conf.sections())
		for section in sections:
			self.run_driver(section)

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

	def users(self):
		self.db.define_table('users',
			StrColumn('first_name'),
			StrColumn('last_name'),
			StrColumn('email'),
			IntColumn('age', default=18),
			DateTimeColumn('registered', default=datetime.datetime.now),
			primarykey = 'email',
		)
		self.assertIn('users', self.db)

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


if __name__=='__main__':
	print 'Testing using %s as driver...' % args.driver
	unittest.main()
