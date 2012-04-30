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
	XMLNode('span', _class=['highlight'])
	>>> print a
	<div><span class='highlight' /></div>
	
	One attribute, '_class' is treated specially. It is always created as a
	sequence, so that ...
	
	>>> a._class.append('lowlight')
	
	should never raise an error, so long as only sequences are assigned to _class
	'''
	def __init__(self, *children, **attributes):
		super(XMLNode, self).__init__(*children, **attributes)
		self.attributes['_class'] = sequence(self.attributes.get('_class',[]))
	
	def __str__(self):
		return ('<%(name)s%(attr)s>%(kids)s</%(name)s>' if len(self.children) else '<%(name)s%(attr)s />') % dict(
			name=self.name,
			kids=''.join(map(_xml,self.children)),
			attr=self._render_attrs(),
		)

	def __repr__(self):
		return '%s(%s)'%(self.__class__.__name__,', '.join([repr(self.name)] + \
		  map(repr,self.children) + \
		  ['%s=%r'%(k,v) for k,v in self.attributes.items() if len(sequence(v))]))

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
		return ''.join(' %s=%r'%(k.replace('_','-'),v) for k,v in items if len(sequence(v)))

def Hyper(href, *children, **attributes):
	'''Helper function for creating hyperlinks

	>>> print Hyper('http://www.google.com', 'Google')
	<a href='http://www.google.com'>Google</a>
	'''
	attributes['_href'] = href
	return A(*children, **attributes)

def Image(src, alt=None, **attributes):
	'''Helper function for creating images

	>>> print Image('favicon.ico')
	<img src='favicon.ico' />
	'''
	attributes['_src'] = src
	if alt:
		attributes['_alt'] = alt
	return IMG(**attributes)

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
	
	>>> print HTMLDoc()
	<!DOCTYPE HTML>
	<html><head><meta charset='utf-8' /></head><body></body></html>
	
	Keyword parameters:
	
	conditional=True : Wraps start <html> tag in conditional comments, setting
	  css classes on the element corresponding to browser
	  (see paulirish.com/2008/conditional-stylesheets-vs-css-hacks-answer-neither/
	   for more information.)
	
	>>> print HTMLDoc(conditional=True)
	<!DOCTYPE HTML>
	<!--[if lt IE 7]><html class='ie6'><![endif]--><!--[if IE 7]><html class='ie7'><![endif]--><!--[if IE 8]><html class='ie8'><![endif]--><!--[if IE 9]><html class='ie9'><![endif]--><!--[if (gt IE 9)|!(IE)]><!--><html><!--<![endif]--><head><meta charset='utf-8' /></head><body></body></html>
	
	
	title='' : Automatically includes a title tag in the head.
	
	>>> print HTMLDoc(title='Welcome to Siteland')
	<!DOCTYPE HTML>
	<html><head><meta charset='utf-8' /><title>Welcome to Siteland</title></head><body></body></html>
	
	
	doctype='html' : Set the document type header of the document. Defaults to
	  HTML5. Possible values can be found as HTMLDoc.doctypes.keys()
	
	>>> print HTMLDoc(doctype='xhtml11', no_js=True, conditional=True)
	<!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
	<!--[if lt IE 7]><html class='ie6 no-js'><![endif]--><!--[if IE 7]><html class='ie7 no-js'><![endif]--><!--[if IE 8]><html class='ie8 no-js'><![endif]--><!--[if IE 9]><html class='ie9 no-js'><![endif]--><!--[if (gt IE 9)|!(IE)]><!--><html class='no-js'><!--<![endif]--><head><meta charset='utf-8' /></head><body></body></html>
	
	
	charset='utf-8' : Sets the character set for the document. Set to a false value
	to prevent such a meta tag being included in the document.
	
	>>> print HTMLDoc(charset='iso-8859-1')
	<!DOCTYPE HTML>
	<html><head><meta charset='iso-8859-1' /></head><body></body></html>
	>>> print HTMLDoc(charset=None)
	<!DOCTYPE HTML>
	<html><head></head><body></body></html>
	
	
	includes=[] : A list of arguments to HTMLDoc.include. Members may be nodes,
	  or strings which are interpretted as paths
	
	>>> a,b = HTMLDoc(charset='', includes=['/static.css', XML('123')]).head
	>>> print a.name, a._href, a._type
	link /static.css text/css
	>>> print b
	123
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
	#Aliases
	doctypes.html = doctypes.html5
	doctypes.html4 = doctypes.html_strict
	doctypes.strict = doctypes.html_strict
	doctypes.transitional = doctypes.html_transitional
	doctypes.frameset = doctypes.html_frameset
	doctypes.xhtml = doctypes.xhtml11

	def __init__(self, *children, **attributes):
		self.conditional = attributes.pop('conditional', False)
		title = attributes.pop('title','')
		attributes.setdefault('doctype','html')
		no_js = attributes.pop('no_js', False)
		includes = attributes.pop('includes', [])
		charset = attributes.pop('charset','utf-8')
		if title:
			includes.insert(0, TITLE(title))
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

	def parse_doctype(self):
		dt = self.doctypes.get(self.doctype,self.doctype)
		m = re.match(r'[hH][tT][mM][lL]( PUBLIC "-//W3C//DTD (?P<type>X?HTML) (?P<version>[0-9.]+)( (?P<variant>Strict|Transitional|Frameset))?//EN")?', dt)
		if not m:
			raise Exception('Unable to parse doctype: %s'%dt)
		else:
			m = container(m.groupdict())
			if m.type is None and m.version is None and m.variant is None:
				m.type = 'HTML'
				m.version = '5'
			if m.type == 'HTML' and m.version == '4.01' and m.variant is None:
				m.variant = 'Strict'
			return m

	def find_deprecated(self):
		'''Walks the node tree, checking for deprecated elements.
		
		'''
		dt_info = self.parse_doctype()
		if (dt_info.type, dt_info.version) == ('HTML','5'):
			deprecated = set("""acronym applet basefont big center dir font frame
				frameset isindex noframes strike tt u""".split())
		elif (dt_info.type, dt_info.version) == ('XHTML', '1.1'):
			deprecated = set("""applet area article aside audio base basefont
				bdi bdo canvas center col colgroup command datalist del details
				dir embed figcaption figure font footer frame frameset header
				hgroup iframe ins isindex keygen map mark menu meter nav noframes
				output progress rp rt ruby s section source strike summary tbody
				tfoot thead time track u video wbr""".split())
		else:
			deprecated = set("""article aside audio bdi canvas command datalist
				details embed figcaption figure footer header hgroup keygen mark
				meter nav output progress rp rt ruby section source summary time
				track video wbr""".split())
			if dt_info.variant in ('Transitional','Strict'):
				deprecated.update("""frame frameset""".split())
			if dt_info.variant == 'Strict':
				deprecated.update("""applet basefont center dir font iframe isindex menu noframes strike u""".split())
		for depth,element in self.walk(lambda x:isinstance(x,Node) and x.name in deprecated):
			yield depth,element

if __name__=='__main__':
	import doctest
	doctest.testmod()
