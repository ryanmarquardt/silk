#!/usr/bin/env python

from StringIO import StringIO
import re
import sys

import io

class StencilBase(object):
	'''Base class for template engines.

	>>> class Web2pyStencil(StencilBase):
	...   opener, closer = '{{', '}}'
	...   indent = '  '
	>>> parse = Web2pyStencil.parse
	>>> parse("{{=123}}")
	'sys.stdout.write(str(123))\\n'
	
	>>> parse("123{{if True:}}456{{pass}}", out=sys.stdout)
	sys.stdout.write('123')
	if True:
	  sys.stdout.write('456')

	>>> class ErbStencil(StencilBase):
	...   opener, closer = '<%', '%>'
	>>> ErbStencil.parse("You have <%= 'no' if x==0 else x %> messages", out=sys.stdout)
	sys.stdout.write('You have ')
	sys.stdout.write(str('no' if x==0 else x))
	sys.stdout.write(' messages')
	
	>>> parse("Uncompleted substitution {{}")
	Traceback (most recent call last):
		...
	SyntaxError: Unclosed substitution
	
	>>> parse("""This is a {{='multiline'
	... }} message.""", out=sys.stdout)
	sys.stdout.write('This is a ')
	sys.stdout.write(str('multiline'))
	sys.stdout.write(' message.')
	
	>>> parse('{{="""This is a \\nmultiline message."""}}', out=sys.stdout)
	sys.stdout.write(str("""This is a 
	multiline message."""))

	Subs can contain whole blocks, but can't contain anything outside the sub.
	>>> parse('{{if more_complicated:\\n  it(should, work, anyway)\\nelse:\\n  exit(0)}}{{="This always prints"}}', out=sys.stdout)
	if more_complicated:
	  it(should, work, anyway)
	else:
	  exit(0)
	sys.stdout.write(str("This always prints"))
	
	The 'pass' keyword takes on new meaning as a block-ending token
	>>> parse('{{pass}}')
	Traceback (most recent call last):
		...
	SyntaxError: Got dedent outside of block

	Opening sequences aren't parsed inside substitutions
	>>> parse("{{='{{'}}")
	"sys.stdout.write(str('{{'))\\n"

	Closing sequences are, however.
	>>> parse("{{='Hello: }}'}}")
	Traceback (most recent call last):
		...
	SyntaxError: EOL while scanning string literal
	>>> parse("{{='Hello }'+'}'}}", out=sys.stdout)
	sys.stdout.write(str('Hello }'+'}'))
	'''
	
	writer='sys.stdout.write'
	indent = '\t'
	
	def __init__(self, path_or_file, filename='<string>'):
		if isinstance(path_or_file, basestring):
			path_or_file = open(path_or_file, 'r')
		self.file = path_or_file
		self.filename = getattr(path_or_file, 'name', filename)
		self.subs = {
			'=\s*':self.on_equal_sign,
		}

	def dedent(self, token):
		return token == 'pass'

	def on_equal_sign(self, token, remainder):
		return '%s(str(%s))' % (self.writer, remainder)

	@classmethod
	def parse(cls, data, out=None):
		self = cls(StringIO(data))
		return self.compile(out)

	def compile(self, out=None):
		_return = out is None
		if _return:
			out = StringIO()
		i,level = self.indent,0
		insub,multiline = False,''
		for lineno,line in enumerate(self.file, 1):
			multiline,line,text,col = '',multiline+line,line,0
			while line:
				if insub:
					e,found,line = line.partition(self.closer)
					if not found:
						multiline += e
						break
					e = e.strip()
					if e:
						for pat,func in self.subs.items():
							m = re.match('(%s)'%pat, e)
							if m:
								col += m.end()
								e = e[m.end():]
								print >>out, '%s%s'%(i*level,func(*(m.groups()+(e,))))
								break
						else:
							d = self.dedent(e)
							if d or any(e.startswith(b) for b in ('elif','else','except','finally')):
								level -= 1
								if level < 0:
									raise SyntaxError('Got dedent outside of block', (self.filename,lineno,col,text))
							if not d:
								print >>out, '%s%s'%(i*level,e)
							if e[-1]==':':
								level += 1
						test = e
						if test[-1]==':': #Add stubs to make line-by-line syntax checking work with blocks
							if test[:2] == 'el':
								test='if 1:pass\n'+test
							elif test.startswith('except') or test.startswith('finally'):
								test='try:pass\n'+test
							test+='\n\tpass'
						try:
							compile(test, self.filename, 'exec')
						except SyntaxError, err:
							raise SyntaxError(err.msg, (self.filename,lineno,col+err.offset,text))
					col += len(e)+len(self.closer)
				else:
					p,found,line = line.partition(self.opener)
					if not found:
						multiline += p
						break
					if p: print >>out, '%s%s(%r)'%(i*level,self.writer,p)
					col += len(p)+len(self.opener)
				insub = not insub
		if multiline:
			if insub:
				raise SyntaxError('Unclosed substitution', (self.filename,lineno,col,text))
			else:
				print >>out, '%s%s(%r)'%(i*level,self.writer,multiline)
		if _return:
			return out.getvalue()

class Web2pyStencil(StencilBase):
	opener = '{{'
	closer = '}}'

	def __init__(self, *args, **kwargs):
		StencilBase.__init__(self, *args, **kwargs)
		self.subs['extend\s+'] = self.on_extend

	def on_extend(self, token, remainder):
		return '#Extending %s' % remainder

class ErbStencil(StencilBase):
	opener = '<%'
	closer = '%>'

if __name__=='__main__':
	import doctest
	doctest.testmod()
