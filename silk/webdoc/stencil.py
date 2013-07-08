#!/usr/bin/env python

from StringIO import StringIO
import re
import sys

class INDENT:pass
class DEDENT:pass

class IndentingPrinter(object):
	def __init__(self, stream, indent):
		self.stream = stream
		self.indent = indent
		self.level = 0

	def __call__(self, text):
		if text is INDENT:
			self.level += 1
		elif text is DEDENT:
			self.level -= 1
			if self.level < 0:
				raise ValueError("Can't have negative indent")
		else:
			print >>self.stream, '%s%s' % (self.indent * self.level, text)

class StencilFile(object):
	def __init__(self, opener, closer, path_or_file, filename='<string>'):
		self.opener = opener
		self.closer = closer
		if isinstance(path_or_file, basestring):
			path_or_file = open(path_or_file, 'r')
		self.file = path_or_file
		self.filename = getattr(path_or_file, 'name', filename)
		self.iter = iter(self)

	def next(self):
		return self.iter.next()

	def __iter__(self):
		insub, multiline = False, ''
		for lineno, line in enumerate(self.file, 1):
			multiline, line, text, column = '', multiline+line, line, 0
			while line:
				split = self.closer if insub else self.opener
				token, found, line = line.partition(split)
				if not found:
					multiline += token
					break
				if insub:
					token = token.strip()
				if token:
					yield lineno, column, insub, token, text
				column += len(token) + len(split)
				insub = not insub
		if multiline or insub:
			if insub:
				raise SyntaxError('Unclosed substitution', (self.filename,lineno,column,text))
			else:
				yield lineno, column, insub, multiline, text

class Stencil(object):
	"""
	>>> erb = Stencil('<%', '%>')
	>>> erb.compile('b.stencil', out=sys.stdout)
	# extend 'a.stencil'
	sys.stdout.write('abc\\n')
	# include ''
	sys.stdout.write('\\ndef\\n')
	sys.stdout.write('\\nghi\\n')

	>>> exec erb.compile('b.stencil')
	abc
	<BLANKLINE>
	def
	<BLANKLINE>
	ghi

	>>> parse = Stencil('{{', '}}', '  ').parse
	>>> parse("{{=123}}")
	'sys.stdout.write(str(123))\\n'

	>>> parse("123{{if True:}}456{{pass}}", out=sys.stdout)
	sys.stdout.write('123')
	if True:
	  sys.stdout.write('456')

	>>> erb.parse("You have <%= 'no' if x==0 else x %> messages", out=sys.stdout)
	sys.stdout.write('You have ')
	sys.stdout.write(str('no' if x==0 else x))
	sys.stdout.write(' messages')

	>>> parse("Uncompleted substitution {{")
	Traceback (most recent call last):
		...
	SyntaxError: Unclosed substitution

	>>> parse('''This is a {{='multiline'
	... }} message.''', out=sys.stdout)
	sys.stdout.write('This is a ')
	sys.stdout.write(str('multiline'))
	sys.stdout.write(' message.')

	>>> parse("{{='''This is a \\nmultiline message.'''}}", out=sys.stdout)
	sys.stdout.write(str('''This is a 
	multiline message.'''))

	>>> parse('{{if more_complicated:\\n  it(should, work, anyway)\\nelse:\\n  exit(0)}}{{="This always prints"}}', out=sys.stdout)
	if more_complicated:
	  it(should, work, anyway)
	else:
	  exit(0)
	sys.stdout.write(str("This always prints"))

	>>> parse("{{if a:}}{{if b:}}{{if c:}}{{=True}}{{pass}}{{pass}}{{pass}}", out=sys.stdout)
	if a:
	  if b:
	    if c:
	      sys.stdout.write(str(True))

	>>> parse('{{pass}}')
	Traceback (most recent call last):
		...
	SyntaxError: Got dedent outside of block

	>>> parse("{{='{{'}}")
	"sys.stdout.write(str('{{'))\\n"
	"""
	def __init__(self, opener=None, closer=None, indent='\t', writer='sys.stdout.write'):
		if opener:
			self.opener = opener
		if closer:
			self.closer = closer
		self.writer = writer
		self.indent = indent
		self.subs = {
			'=\s*':self.on_equal_sign,
			'extend$|extend\s+':self.on_extend,
			'include$|include\s+':self.on_include,
		}

	def is_dedent(self, token):
		return token == 'pass'

	def on_equal_sign(self, printer, token, remainder):
		printer('%s(str(%s))' % (self.writer, remainder))

	def open(self, path):
		return __builtins__.open(path, 'r')

	def on_extend(self, printer, token, remainder):
		printer('# extend %r' % remainder)
		this = self.sources.pop(-1)
		self.sources.append(StencilFile(self.opener, self.closer, self.open(remainder), remainder))
		self.sources[-1].extends = this

	def on_include(self, printer, token, remainder):
		printer('# include %r' % remainder)
		if remainder:
			self.sources.append(StencilFile(self.opener, self.closer, self.open(remainder), remainder))
		elif hasattr(self.sources[-1], 'extends'):
			this = self.sources[-1]
			self.sources.append(this.extends)
			del this.extends

	def interpret(self, iprint, lineno, column, python, text, orig):
		filename = self.sources[-1].filename
		for pattern, function in self.subs.items():
			match = re.match('(%s)' % pattern, text)
			if match:
				column += match.end()
				text = text[match.end():]
				function(iprint, *(match.groups()+(text,)))
				break
		else:
			dedent = self.is_dedent(text)
			if dedent or any(text.startswith(b) for b in ('elif', 'else', 'except', 'finally')):
				try:
					iprint(DEDENT)
				except ValueError:
					raise SyntaxError('Got dedent outside of block', (filename, lineno, column, orig))
			stub = text
			if stub[-1] == ':':
				if stub[:2] == 'el':
					stub = 'if 1:pass\n'+stub
				elif any(map(stub.startswith, ('except','finally'))):
					stub = 'try:pass\n'+stub
				stub += '\n\tpass'
			try:
				compile(stub, filename, 'exec')
			except SyntaxError, err:
				raise SyntaxError(err.msg, (filename, lineno, column+err.offset, orig))
			if not dedent:
				if python:
					iprint(text)
					if text[-1] == ':':
						iprint(INDENT)
				else:
					iprint('%s(%r)' % (self.writer,text))

	def sequence(self):
		while self.sources:
			try:
				values = self.sources[-1].next()
			except StopIteration:
				del self.sources[-1]
				continue
			if values[3]:
				yield values

	def parse(self, data, out=None):
		return self.compile(StringIO(data), out=out)

	def compile(self, path_or_file, filename='<string>', out=None):
		self.sources = [StencilFile(self.opener, self.closer, path_or_file, filename)]
		_return = out is None
		if _return:
			out = StringIO()
		iprint = IndentingPrinter(out, self.indent)
		for lineno, col, python, text, orig in self.sequence():
			self.interpret(iprint, lineno, col, python, text, orig)
		if _return:
			return out.getvalue()

if __name__ == '__main__':
	import doctest
	doctest.testmod()
