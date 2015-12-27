from ... import *
from ..node import *

import collections
from functools import partial
from xml.sax.saxutils import escape as xmlescape, unescape as xmlunescape
import re

__all__ = ['xmlescape', 'xmlunescape']

def _all(func_or_class):
    __all__.append(func_or_class.__name__)
    return func_or_class


def _xml(value, attr=False):
	if is_sequence(value):
		return (' ' if attr else '').join(map(_xml,value))
	elif isinstance(value, Node):
		return str(value)
	else:
		return xmlescape(str(value))

@_all
class XMLEntity(Entity):
	@staticmethod
	def start(name, **attributes):
		return XMLStartEntity(name, **attributes)

	@staticmethod
	def end(name, **attributes):
		return XMLEndEntity(name, **attributes)

	@staticmethod
	def closed(name, **attributes):
		return XMLClosedEntity(name, **attributes)

class XMLStartEntity(XMLEntity):
	def __str__(self):
		return '<%s%s>' % (self.name, ''.join(' %s=%r' % i for i in list(self.attributes.items())))

class XMLEndEntity(XMLEntity):
	def __str__(self):
		return '</%s>' % self.name

class XMLClosedEntity(XMLEntity):
	def __str__(self):
		return '<%s%s />' % (self.name, ''.join(' %s=%r' % i for i in list(self.attributes.items())))

@_all
class XMLNode(Node):
	'''Node which is represented as xml.
	
	>>> print(XMLNode.new('a')('My home page', href='http://homepage.com'))
	<a href='http://homepage.com'>My home page</a>
	
	Literals are escaped properly when rendering.
	
	>>> print(XMLNode.new('a')('>>> Click Here! <<<', href='/index?a=1&b=2'))
	<a href='/index?a=1&amp;b=2'>&gt;&gt;&gt; Click Here! &lt;&lt;&lt;</a>
	
	Attributes that are empty sequences (excluding strings) will be ignored:
	
	>>> print(XMLNode.new('div')('abc', _class=[]))
	<div>abc</div>
	>>> print(XMLNode.new('div')('abc', _class=''))
	<div class=''>abc</div>
	>>> a = XMLNode.new('div')()
	>>> a.add('span.highlight')
	XMLNode('span')(_class=['highlight'])
	>>> print(a)
	<div><span class='highlight' /></div>
	'''
	def __init__(self, *children, **attributes):
		if '_class' in attributes:
			attributes['_class'] = sequence(attributes['_class'])
		super(XMLNode, self).__init__(*children, **attributes)
		#self.attributes['_class'] = sequence(self.attributes.get('_class',[]))
	
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
		node = XMLNode.new(name)(**dict((k,' '.join(vs)) for k,vs in list(props.items())))
		self.append(node)
		return node
		
	def _render_attrs(self):
		return ''.join(' %s=%r'%(k.replace('_','-'),_xml(v,attr=True)) for k,v in list(self._real_attrs().items()) if len(sequence(v)))
		
	def __setitem__(self, key, value):
		if key in ('class','_class'):
			value = sequence(value)
		super(XMLNode, self).__setitem__(key, value)

class XMLNoChildNode(XMLNode):
	'''Node which is represented as xml, and forbidden to have children.
	
	>>> XMLNoChildNode.new('br')()
	XMLNoChildNode('br')()
	>>> print(XMLNoChildNode.new('hr')())
	<hr />
	>>> print(XMLNoChildNode.new('meta')(charset='utf-8'))
	<meta charset='utf-8' />
	>>> XMLNoChildNode.new('br')('ignored', _not='this')
	XMLNoChildNode('br')(_not='this')
	'''
	def __init__(self, *children, **attributes):
		super(XMLNoChildNode, self).__init__(**attributes)

class XMLNotEmptyNode(XMLNode):
	'''XMLNode which always renders with a start and end tag.
	
	>>> print(XMLNotEmptyNode.new('head')())
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

normal_tags = {
    'A', 'ABBR', 'ACRONYM', 'ADDRESS', 'APPLET', 'B', 'BDO', 'BIG',
    'BLOCKQUOTE', 'BUTTON', 'CAPTION', 'CENTER', 'CITE', 'CODE', 'COLGROUP',
    'DD', 'DEL', 'DFN', 'DIR', 'DL', 'DT', 'EM', 'FIELDSET', 'FONT', 'FORM',
    'FRAMESET', 'HEAD', 'I', 'IFRAME', 'INS', 'KBD', 'LABEL', 'LEGEND', 'LI',
    'MAP', 'MENU', 'NOFRAMES', 'NOSCRIPT', 'OBJECT', 'OL', 'OPTGROUP',
    'OPTION', 'P', 'PRE', 'Q', 'S', 'SAMP', 'SELECT', 'SMALL', 'SPAN',
    'STRIKE', 'STRONG', 'STYLE', 'SUB', 'SUP', 'TABLE', 'TBODY', 'TD',
    'TEXTAREA', 'TFOOT', 'TH', 'THEAD', 'TITLE', 'TR', 'TT', 'U', 'UL', 'VAR',
    'XMP',
}


for name in normal_tags:
    globals()[name] = type(name, (XMLNode,), {'name': name.lower()})
    __all__.append(name)


nochild_tags = {
    'AREA', 'BASE', 'BASEFONT', 'BR', 'COL', 'FRAME', 'HR', 'IMG', 'INPUT',
    'LINK', 'PARAM',
}


for name in nochild_tags:
    globals()[name] = type(name, (XMLNoChildNode,), {'name': name.lower()})
    __all__.append(name)


notempty_tags = {
    'HEAD', 'DIV', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
}


for name in notempty_tags:
    globals()[name] = type(name, (XMLNotEmptyNode,), {'name': name.lower()})
    __all__.append(name)


@_all
class Form(FORM):
	'''
	'''
	def __init__(self, *children, **attributes):
		FORM.__init__(self, *children, **attributes)
		self.setdefault('_method','POST')
		self.setdefault('_enctype','multipart/form-data')

@_all
class COMMENT(XMLNode):
	'''Includes comments.
	
	>>> print(COMMENT('This is a comment'))
	<!--This is a comment-->
	>>> print(COMMENT('This is also', ' a comment'))
	<!--This is also a comment-->
	'''
	def __str__(self):
		return '<!--%s-->'%''.join(map(str,self.children))

@_all
class CONDITIONAL_COMMENT(XMLNode):
	'''Used to comment out text conditionally by browser
	
	>>> print(CONDITIONAL_COMMENT('lt IE 7', 'Your browser is IE before version 7'))
	<!--[if lt IE 7]>Your browser is IE before version 7<![endif]-->
	>>> print(CONDITIONAL_COMMENT('(gt IE 9)|!(IE)', 'Your browser is IE after version 7 or not IE', uncomment=True))
	<!--[if (gt IE 9)|!(IE)]><!-->Your browser is IE after version 7 or not IE<!--<![endif]-->
	'''
	def __init__(self, condition, *children, **attributes):
		self.name = condition
		self.uncomment = attributes.pop('uncomment', False)
		XMLNode.__init__(self, *children)
	
	def __str__(self):
		return ('<!--[if %(name)s]><!-->%(kids)s<!--<![endif]-->' if self.uncomment else '<!--[if %(name)s]>%(kids)s<![endif]-->') % dict(
			name=self.name,
			kids=''.join(map(_xml,self.children))
		)

@_all
class XML(XMLNode):
	'''Renders text without escaping it.
	
	>>> print(XML('<abc />'))
	<abc />
	>>> x = '123'
	>>> print(XML('<a>', x, '</a>'))
	<a>123</a>
	'''
	def __str__(self):
		return ''.join(map(str,self.children))

NBSP = XML('&nbsp;')

__all__.append('NBSP')


@_all
class CAT(XMLNode):
	'''Concatenates child nodes.
	
	>>> from functools import partial
	>>> DIV = XMLNode.new('div')
	>>> print(CAT('a', 'b'))
	ab
	>>> print(CAT(DIV('a'), DIV('b'), DIV('c')))
	<div>a</div><div>b</div><div>c</div>
	'''
	def __str__(self):
		return ''.join(map(_xml,self.children))

@_all
class META(XMLNoChildNode):
	'''
	
	>>> print(META.charset('utf-16'))
	<meta charset='utf-16' />
	>>> print(META.value('application-name', 'examples'))
	<meta name='application-name' content='examples' />
	>>> print(META.http_equiv('X-UA-Compatible', 'IE=edge'))
	<meta http-equiv='X-UA-Compatible' content='IE=edge' />
	'''
	name = 'meta'
	
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
		items.extend(list(ra.items()))
		return ''.join(' %s=%r'%(k.replace('_','-'),v) for k,v in items if len(sequence(v)))


@_all
def Hyper(href, *children, **attributes):
	'''Helper function for creating hyperlinks

	>>> print(Hyper('http://www.google.com', 'Google'))
	<a href='http://www.google.com'>Google</a>
	'''
	attributes['_href'] = href
	return A(*children, **attributes)


@_all
def Image(src, alt=None, **attributes):
	'''Helper function for creating images

	>>> print(Image('favicon.ico'))
	<img src='favicon.ico' />
	'''
	r = IMG(**attributes)
	r['_src'] = src
	if alt:
		r.setdefault('_alt',alt)
	return r


@_all
class SCRIPT(XMLNode):
	'''
	
	>>> print(SCRIPT())
	<script></script>
	>>> print(SCRIPT('var abc = "123";', type='text/javascript'))
	<script type='text/javascript'><!--
	var abc = "123";
	//--></script>
	
	'''
	name = 'script'
	
	def __str__(self):
		if self.children:
			return '<script%(attr)s><!--\n%(kids)s\n//--></script>' % dict(
				attr=self._render_attrs(),
				kids=''.join(map(_xml,self.children)),
			)
		else:
			return '<script%s></script>'%self._render_attrs()


Javascript = partial(SCRIPT, type='text/javascript')
__all__.append('Javascript')


@_all
class BODY(XMLNotEmptyNode):
	'''
	'''
	name = 'body'


@_all
class Body(BODY):
	def __init__(self, *children, **attributes):
		self.conditional = attributes.pop('conditional', False)
		XMLNode.__init__(self, *children, **attributes)
		
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


@_all
class HTML(XMLNotEmptyNode):
	'''Node representing the <html> root element of an html document. Using this
	class directly is not recommended. Instead use the more featureful HTMLDoc().
	
	>>> print(HTML())
	<!DOCTYPE html>
	<html></html>
	>>> print(HTML(doctype='12345'))
	<!DOCTYPE 12345>
	<html></html>
	>>> print(HTML(HEAD(), BODY()))
	<!DOCTYPE html>
	<html><head></head><body></body></html>
	'''
	name = 'html'
	def __init__(self, *children, **attributes):
		self.doctype = attributes.pop('doctype', 'html')
		XMLNotEmptyNode.__init__(self, *children, **attributes)
		
	def __str__(self):
		return '<!DOCTYPE %(doctype)s>\n<%(name)s%(attr)s>%(kids)s</%(name)s>' % dict(
			doctype=self.doctype,
			name=self.name,
			kids=''.join(map(_xml,self.children)),
			attr=self._render_attrs(),
		)


@_all
class HTMLDoc(HTML):
	'''Class representing a complete (X)HTML document.
	
	>>> print(HTMLDoc())
	<!DOCTYPE HTML>
	<html><head><meta charset='utf-8' /></head><body></body></html>
	
	Keyword parameters:
	
	conditional=True : Wraps start <html> tag in conditional comments, setting
	  css classes on the element corresponding to browser
	  (see paulirish.com/2008/conditional-stylesheets-vs-css-hacks-answer-neither/
	   for more information.)
	
	>>> print(HTMLDoc(conditional=True))
	<!DOCTYPE HTML>
	<!--[if lt IE 7]><html class='ie6'><![endif]--><!--[if IE 7]><html class='ie7'><![endif]--><!--[if IE 8]><html class='ie8'><![endif]--><!--[if IE 9]><html class='ie9'><![endif]--><!--[if (gt IE 9)|!(IE)]><!--><html><!--<![endif]--><head><meta charset='utf-8' /></head><body></body></html>
	
	
	title='' : Automatically includes a title tag in the head.
	
	>>> print(HTMLDoc(title='Welcome to Siteland'))
	<!DOCTYPE HTML>
	<html><head><meta charset='utf-8' /><title>Welcome to Siteland</title></head><body></body></html>
	
	
	doctype='html' : Set the document type header of the document. Defaults to
	  HTML5. Possible values can be found as HTMLDoc.doctypes.keys()
	
	>>> print(HTMLDoc(doctype='xhtml11', no_js=True, conditional=True))
	<!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
	<!--[if lt IE 7]><html class='ie6 no-js'><![endif]--><!--[if IE 7]><html class='ie7 no-js'><![endif]--><!--[if IE 8]><html class='ie8 no-js'><![endif]--><!--[if IE 9]><html class='ie9 no-js'><![endif]--><!--[if (gt IE 9)|!(IE)]><!--><html class='no-js'><!--<![endif]--><head><meta charset='utf-8' /></head><body></body></html>
	
	
	charset='utf-8' : Sets the character set for the document. Set to a false value
	to prevent such a meta tag being included in the document.
	
	>>> print(HTMLDoc(charset='iso-8859-1'))
	<!DOCTYPE HTML>
	<html><head><meta charset='iso-8859-1' /></head><body></body></html>
	>>> print(HTMLDoc(charset=None))
	<!DOCTYPE HTML>
	<html><head></head><body></body></html>
	
	
	includes=[] : A list of arguments to HTMLDoc.include. Members may be nodes,
	  or strings which are interpretted as paths
	
	>>> a,b = HTMLDoc(charset='', includes=['/static.css', XML('123')]).head
	>>> print(a.name, a._href, a._type)
	link /static.css text/css
	>>> print(b)
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
		return self.walk(lambda x:isinstance(x,Node) and x.name in deprecated)

