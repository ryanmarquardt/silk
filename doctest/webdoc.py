#!/usr/bin/env python

import unittest

from silk.webdoc.css import *
from silk.webdoc.node import *
from silk.webdoc.html import *
from silk.webdoc.stencil import *

class DocBase(unittest.TestCase):
	def setUp(self):
		pass

class HTMLEntityTest(DocBase):
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

class StencilTest(unittest.TestCase):
	def run_parsed(self, code):
		io = StringIO()
		exec code
		return io.getvalue()

class W2PStencilTest(StencilTest):
	def setUp(self):
		self.parse = Stencil('{{', '}}', writer='io.write').parse

	def test_basic_subsitution(self):
		x = self.parse("{{=123}}")
		self.assertEqual(x, "io.write(str(123))\n")
		self.assertEqual(self.run_parsed(x), '123')

	def test_basic_block(self):
		x = self.parse("123{{if True:}}456{{pass}}")
		self.assertEqual(x, "io.write('123')\nif True:\n\tio.write('456')\n")
		self.assertEqual(self.run_parsed(x), "123456")

	def test_unclosed_sub(self):
		with self.assertRaisesRegexp(SyntaxError, "Unclosed substitution"):
			self.parse("Uncompleted substitution {{")

	def test_multiline_msg(self):
		x = self.parse("{{='''This is a \nmultiline message.'''}}")
		self.assertEqual(x, "io.write(str('''This is a \nmultiline message.'''))\n")
		self.assertEqual(self.run_parsed(x), "This is a \nmultiline message.")

class ErbStencilTest(StencilTest):
	def setUp(self):
		self.parse = Stencil('<%', '%>', writer='io.write').parse

	def test_embedded_subs(self):
		x = self.parse("You have <%= 'no' if x==0 else x %> messages")
		self.assertEqual(x, "io.write('You have ')\nio.write(str('no' if x==0 else x))\nio.write(' messages')\n")

if __name__ == '__main__':
	unittest.main()
