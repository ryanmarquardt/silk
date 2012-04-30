from common import *
from node import *

import collections
from functools import partial
from xml.sax.saxutils import escape as xmlescape, unescape as xmlunescape
import re

def _xml(value, attr=False):
	if is_sequence(value):
		return (' ' if attr else '').join(map(_xml,value))
	elif isinstance(value, Node):
		return str(value)
	else:
		return xmlescape(str(value))

class XMLNode(Node):
	'''Node which is represented as xml.
	
	>>> print XMLNode('a', 'My home page', href='http://homepage.com')
	<a href='http://homepage.com'>My home page</a>
	
	Literals are escaped properly when rendering.
	
	>>> print XMLNode('a', '>>> Click Here! <<<', href='/index?a=1&b=2')
	<a href='/index?a=1&amp;b=2'>&gt;&gt;&gt; Click Here! &lt;&lt;&lt;</a>
	
	Attributes that are empty sequences (excluding strings) will be ignored:
	
	>>> print XMLNode('div', 'abc', _class=[])
	<div>abc</div>
	>>> print XMLNode('div', 'abc', _class='')
	<div class=''>abc</div>
	>>> a = XMLNode('div')
	>>> a.add('span.highlight')
	XMLNode('span', _class='highlight')
	>>> print a
	<div><span class='highlight' /></div>
	'''
	def __str__(self):
		return ('<%(name)s%(attr)s>%(kids)s</%(name)s>' if len(self.children) else '<%(name)s%(attr)s />') % dict(
			name=self.name,
			kids=''.join(map(_xml,self.children)),
			attr=self._render_attrs(),
		)

	def add(self, selector):
		name = None
		props = collections.defaultdict(list)
		maps = {'.':'_class','#':'_id'}
		for part in re.findall('([.#]?[-_a-zA-Z0-9]+)', selector):
			props[maps.get(part[0])].append(part[1:] if part[0] in maps else part)
		name = props.pop(None, ['div'])[0]
		node_cls = globals().get(name.title()) or globals().get(name.upper()) or partial(XMLNode, name)
		node = node_cls(**dict((k,' '.join(vs)) for k,vs in props.items()))
		self.append(node)
		return node
		
	def _render_attrs(self):
		return ''.join(' %s=%r'%(k.replace('_','-'),_xml(v,attr=True)) for k,v in self._real_attrs().items() if len(sequence(v)))
		
class XMLNoChildNode(XMLNode, NoChildrenMixin):
	'''Node which is represented as xml, and forbidden to have children.
	
	>>> XMLNoChildNode('br')
	XMLNoChildNode('br')
	>>> print XMLNoChildNode('hr')
	<hr />
	>>> print XMLNoChildNode('meta', charset='utf-8')
	<meta charset='utf-8' />
	>>> XMLNoChildNode('br', 'ignored', _not='this')
	XMLNoChildNode('br', _not='this')
	'''

class XMLNotEmptyNode(XMLNode):
	'''XMLNode which always renders with a start and end tag.
	
	>>> print XMLNotEmptyNode('head')
	<head></head>
	'''
	def __str__(self):
		return '<%(name)s%(attr)s>%(kids)s</%(name)s>' % dict(
			name=self.name,
			kids=''.join(map(_xml,self.children)),
			attr=self._render_attrs(),
		)

#
###Factory functions for names that don't need special treatment
#
## Normal tags
for tag in """a abbr acronym address applet b bdo big blockquote button
caption center cite code colgroup dd del dfn dir dl dt em fieldset font
form frameset head html i iframe ins kbd label legend li map
menu noframes noscript object ol optgroup option p pre q s samp select
small span strike strong style sub sup table tbody td textarea tfoot th thead
title tr tt u ul var xmp""".split():
	globals()[tag.upper()] = partial(XMLNode,tag.lower())
	assert str(globals()[tag.upper()]()) == '<%s />'%tag.lower(), str(globals()[tag.upper()]())

## NoChild tags
for tag in """area base basefont br col frame hr img input link param""".split():
	globals()[tag.upper()] = partial(XMLNoChildNode,tag.lower())
	assert str(globals()[tag.upper()]()) == '<%s />'%tag.lower(), str(globals()[tag.upper()]())

## NotEmpty tags
for tag in """head div h1 h2 h3 h4 h5 h6""".split():
	globals()[tag.upper()] = partial(XMLNotEmptyNode,tag.lower())
	assert str(globals()[tag.upper()]()) == '<%s></%s>'%(tag.lower(),tag.lower()), str(globals()[tag.upper()]())

class COMMENT(XMLNode, NoAttributesMixin, NoNameMixin):
	'''Includes comments.
	
	>>> print COMMENT('This is a comment')
	<!--This is a comment-->
	>>> print COMMENT('This is also', ' a comment')
	<!--This is also a comment-->
	'''
	def __str__(self):
		return '<!--%s-->'%''.join(map(str,self.children))

class CONDITIONAL_COMMENT(XMLNode, NoAttributesMixin):
	'''Used to comment out text conditionally by browser
	
	>>> print CONDITIONAL_COMMENT('lt IE 7', 'Your browser is IE before version 7')
	<!--[if lt IE 7]>Your browser is IE before version 7<![endif]-->
	>>> print CONDITIONAL_COMMENT('(gt IE 9)|!(IE)', 'Your browser is IE after version 7 or not IE', ornot=True)
	<!--[if (gt IE 9)|!(IE)]><!-->Your browser is IE after version 7 or not IE<!--<![endif]-->
	'''
	def __init__(self, condition, *children, **attributes):
		self.ornot = attributes.pop('ornot', False)
		XMLNode.__init__(self, condition, *children)
	
	def __str__(self):
		return ('<!--[if %(name)s]><!-->%(kids)s<!--<![endif]-->' if self.ornot else '<!--[if %(name)s]>%(kids)s<![endif]-->') % dict(
			name=self.name,
			kids=''.join(map(_xml,self.children))
		)

class XML(XMLNode, NoAttributesMixin, NoNameMixin):
	'''Renders text without escaping it.
	
	>>> print XML('<abc />')
	<abc />
	>>> x = '123'
	>>> print XML('<a>', x, '</a>')
	<a>123</a>
	'''
	def __str__(self):
		return ''.join(map(str,self.children))

class CAT(XMLNode, NoAttributesMixin, NoNameMixin):
	'''Concatenates child nodes.
	
	>>> from functools import partial
	>>> DIV = partial(XMLNode, 'div')
	>>> print CAT('a', 'b')
	ab
	>>> print CAT(DIV('a'), DIV('b'), DIV('c'))
	<div>a</div><div>b</div><div>c</div>
	'''
	def __str__(self):
		return ''.join(map(_xml,self.children))

class META(XMLNoChildNode):
	'''
	
	>>> print META.charset('utf-16')
	<meta charset='utf-16' />
	>>> print META.value('application-name', 'examples')
	<meta name='application-name' content='examples' />
	>>> print META.http_equiv('X-UA-Compatible', 'IE=edge')
	<meta http-equiv='X-UA-Compatible' content='IE=edge' />
	'''
	def __init__(self, **attributes):
		XMLNoChildNode.__init__(self, 'meta', **attributes)
		
	@classmethod
	def charset(cls, charset):
		return cls(_charset=charset)
		
	@classmethod
	def value(cls, name, content=''):
		return cls(_name=name, _content=content)
		
	@classmethod
	def http_equiv(cls, header, content=''):
		return cls(_http_equiv=header, _content = content)
		
	def _render_attrs(self):
		items = []
		ra = self._real_attrs()
		##Assert a particular ordering on some attributes
		if 'name' in ra:
			items.append(('name',ra.pop('name')))
		if 'http_equiv' in ra:
			items.append(('http-equiv',ra.pop('http_equiv')))
		if 'content' in ra:
			items.append(('content',ra.pop('content')))
		items.extend(ra.items())
		return ''.join(' %s=%r'%(k.replace('_','-'),v) for k,v in items)

class SCRIPT(XMLNode):
	'''
	
	>>> print SCRIPT()
	<script></script>
	>>> print SCRIPT('var abc = "123";', type='text/javascript')
	<script type='text/javascript'><!--
	var abc = "123";
	//--></script>
	
	'''
	def __init__(self, *children, **attributes):
		XMLNode.__init__(self, 'script', *children, **attributes)
	
	def __str__(self):
		if self.children:
			return '<script%(attr)s><!--\n%(kids)s\n//--></script>' % dict(
				attr=self._render_attrs(),
				kids=''.join(map(_xml,self.children)),
			)
		else:
			return '<script%s></script>'%self._render_attrs()

Javascript = partial(SCRIPT, type='text/javascript')

class BODY(XMLNotEmptyNode):
	'''
	'''
	def __init__(self, *children, **attributes):
		XMLNotEmptyNode.__init__(self, 'body', *children, **attributes)

class Body(BODY):
	def __init__(self, *children, **attributes):
		self.conditional = attributes.pop('conditional', False)
		XMLNode.__init__(self, 'body', *children, **attributes)
		
	def __str__(self):
		if self.conditional:
			## paulirish.com/2008/conditional-stylesheets-vs-css-hacks-answer-neither/
			return """<!--[if IE 7 ]><body class="ie7"%(attr)s><![endif]-->
<!--[if IE 8 ]><body class="ie8"%(attr)s><![endif]-->
<!--[if IE 9 ]><body class="ie9"%(attr)s><![endif]-->
<!--[if (gt IE 9)|!(IE)]><!--> <body%(attr)s> <!--<![endif]-->%(kids)s</body>""" % dict(
				kids=''.join(map(_xml,self.children)),
				attr=self._render_attrs(),
			)
		else:
			return XMLNotEmptyNode.__str__(self)

class HTML(XMLNotEmptyNode):
	'''Node representing the <html> root element of an html document. Using this
	class directly is not recommended. Instead use the more featureful HTMLDoc().
	
	>>> print HTML()
	<!DOCTYPE html>
	<html></html>
	>>> print HTML(doctype='12345')
	<!DOCTYPE 12345>
	<html></html>
	>>> print HTML(HEAD(), BODY())
	<!DOCTYPE html>
	<html><head></head><body></body></html>
	'''
	def __init__(self, *children, **attributes):
		self.doctype = attributes.pop('doctype', 'html')
		XMLNotEmptyNode.__init__(self, 'html', *children, **attributes)
		
	def __str__(self):
		return '<!DOCTYPE %(doctype)s>\n<%(name)s%(attr)s>%(kids)s</%(name)s>' % dict(
			doctype=self.doctype,
			name=self.name,
			kids=''.join(map(_xml,self.children)),
			attr=self._render_attrs(),
		)

class HTMLDoc(HTML):
	'''Class representing a complete (X)HTML document.
	
	## parameters:
	
	>>> print HTMLDoc(no_js=False, charset=None, conditional=False)
	<!DOCTYPE HTML>
	<html><head></head><body></body></html>
	>>> print HTMLDoc(doctype='xhtml11', conditional=True)
	<!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
	<!--[if lt IE 7]><html class='ie6 no-js'><![endif]--><!--[if IE 7]><html class='ie7 no-js'><![endif]--><!--[if IE 8]><html class='ie8 no-js'><![endif]--><!--[if IE 9]><html class='ie9 no-js'><![endif]--><!--[if (gt IE 9)|!(IE)]><!--><html class='no-js'><!--<![endif]--><head><meta charset='utf-8' /></head><body></body></html>
	'''
	doctypes = container(
		html5='HTML',
		html_strict='HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd"',
		html_transitional='HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"',
		html_frameset='HTML PUBLIC "-//W3C//DTD HTML 4.01 Frameset//EN" "http://www.w3.org/TR/html4/frameset.dtd"',
		xhtml_strict='HTML PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"',
		xhtml_transitional='HTML PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"',
		xhtml_frameset='HTML PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd"',
		xhtml11='HTML PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd"',
	)
	doctypes.html = doctypes.html5
	doctypes.html4 = doctypes.html_strict
	doctypes.strict = doctypes.html_strict
	doctypes.transitional = doctypes.html_transitional
	doctypes.framset = doctypes.html_framset
	doctypes.xhtml = doctypes.xhtml11

	def __init__(self, *children, **attributes):
		self.conditional = attributes.pop('conditional', True)
		attributes.setdefault('doctype','html')
		no_js = attributes.pop('no_js', True)
		includes = attributes.pop('includes', [])
		charset = attributes.pop('charset','utf-8')
		if charset:
			includes.insert(0, META.charset(charset))
		HTML.__init__(self, HEAD(), Body(*children), **attributes)
		self['_class'] = sequence(self.get('_class',[]))
		if no_js:
			self['_class'].append('no-js')
		for path in sequence(includes):
			self.include(path)

	@property
	def head(self): return self[0]
	@head.setter
	def head(self, new): self[0] = new

	@property
	def body(self): return self[1]
	@body.setter
	def body(self, new): self[1] = new

	def include(self, path, type=None, **attributes):
		if isinstance(path, XMLNode):
			node = path
		elif (type is None and path.endswith('.css')) or type=='text/css':
			node = LINK(type='text/css', href=path, **attributes)
			node.setdefault('_rel', 'stylesheet')
		elif (type is None and path.endswith('.ico')) or type=='image/x-icon':
			node = LINK(type='image/x-icon', href=path, **attributes)
			node.setdefault('_rel', 'shortcut icon')
		elif (type is None and path.endswith('.png')) or type=='image/png':
			node = LINK(type='image/png', href=path, **attributes)
		elif (type is None and path.endswith('.js')) or type=='text/javascript':
			node = Javascript(src=path, **attributes)
		elif type is None:
			raise ValueError('Unable to determine mimetype from path, and no type provided')
		else:
			raise ValueError('Unrecognized mimetype %r' % type)
		self.head.append(node)
		return node

	def __str__(self):
		orig_doctype = self.doctype
		self.doctype = self.doctypes[self.doctype]
		if self.conditional:
			result = '<!DOCTYPE %s>\n'%self.doctype
			for cond,cls in [('lt IE 7','ie6'),('IE 7','ie7'),('IE 8','ie8'),('IE 9','ie9')]:
				self.attributes['_class'].insert(0, cls)
				result += str(CONDITIONAL_COMMENT(cond, XML('<html%s>'%self._render_attrs())))
				del self.attributes['_class'][0]
			result += "<!--[if (gt IE 9)|!(IE)]><!--><html%(attr)s><!--<![endif]-->%(kids)s</html>" % dict(
				kids=''.join(map(_xml,self.children)),
				attr=self._render_attrs(),
			)
		else:
			result = super(HTMLDoc, self).__str__()
		self.doctype = orig_doctype
		return result


if __name__=='__main__':
	import doctest
	doctest.testmod()
