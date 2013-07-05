#!/usr/bin/env python

import unittest

from silk.webdoc.css import *
from silk.webdoc.node import *
from silk.webdoc.html import *

class DocBase(unittest.TestCase):
	def setUp(self):
		pass

class EntityTestCase(DocBase):
	pass

class HTMLEntityTest(EntityTestCase):
	def setUp(self):
		class HTMLStartEntity(Entity):
			def __str__(self):
				return '<%s%s>' % (self.name, ''.join(' %s=%r' % i for i in self.attributes.items()))
		self.HTMLStartEntity = HTMLStartEntity
	
	def test_lang_eq_en(self):
		h = self.HTMLStartEntity('html', lang='en')
		self.assertEqual(str(h), "<html lang='en'>")
		h._lang = 'ru'
		self.assertEqual(str(h), "<html lang='ru'>")
		del h['lang']
		self.assertEqual(str(h), "<html>")

class NodeTest(DocBase):
	def test_new(self):
		x = Node.new('x')()
		self.assertEqual(`x`, "Node('x')()")
		y = Node.new('y')(1, 2, 3, a=5)
		self.assertEqual(`y`, "Node('y')(1, 2, 3, _a=5)")
		n = Node.new('n')(r='s')
		n.append('o')
		n.extend(['p', 'z'])
		n[-1] = 'q'
		n['r'] = 'r'
		self.assertEqual(`n`, "Node('n')('o', 'p', 'q', _r='r')")
		n.update(_s='t', r=0)
		del n['r']
		self.assertEqual(n.pop(1), 'p')
		self.assertEqual(`n`, "Node('n')('o', 'q', _s='t')")

	def test_attr_names(self):
		a = Node.new('a')(_class='123')
		self.assertEqual(`a`, "Node('a')(_class='123')")
		self.assertEqual(a['class'], '123')

	def test_missing_attr(self):
		a = Node.new('a')(_class='123')
		self.assertIsNone(a._milk)
		with self.assertRaises(KeyError):
			a['milk']
		with self.assertRaises(KeyError):
			a['_milk']


if __name__ == '__main__':
	unittest.main()
