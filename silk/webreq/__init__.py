r"""

Applications are passed two arguments: one Request object and one Response object
"""

from silk import *

import base64
import collections
import Cookie
import sys
import traceback
import urlparse
import wsgiref.util
import wsgiref.headers

class HTTP(Exception):
	def __init__(self, code, message):
		Exception.__init__(self, code, message)
		self.code = code
		self.message = message

def Redirect(url):
	raise HTTP(303, url)

STATUS_MESSAGES = {
	100:'Continue', 101:'Switching Protocols', 102:'Processing', 200:'OK',
	201:'Created', 202:'Accepted', 203:'Non-Authoritative Information',
	204:'No Content', 205:'Reset Content', 206:'Partial Content',
	207:'Multi-Status', 208:'Already Reported', 226:'IM Used',
	300:'Multiple Choices', 301:'Moved Permanently', 302:'Found',
	303:'See Other', 304:'Not Modified', 305:'Use Proxy', 306:'Switch Proxy',
	307:'Temporary Redirect', 308:'Permanent Redirect', 400:'Bad Request',
	401:'Unauthorized', 402:'Payment Required', 403:'Forbidden',
	404:'Not Found', 405:'Method Not Allowed', 406:'Not Acceptable',
	407:'Proxy Authentication Required', 408:'Request Timeout', 409:'Conflict',
	410:'Gone', 411:'Length Required', 412:'Precondition Failed',
	413:'Request Entity Too Large', 414:'Request-URI Too Long',
	415:'Unsupported Media Type', 416:'Requested Range Not Satisfiable',
	417:'Expectation Failed', 418:"I'm a teapot", 420:'Enhance Your Calm',
	422:'Unprocessable Entity', 423:'Locked', 424:'Failed Dependency',
	425:'Unordered Collection', 426:'Upgrade Required',
	428:'Precondition Required', 429:'Too Many Requests',
	431:'Request Header Fields Too Large', 444:'No Response', 449:'Retry With',
	450:'Blocked by Windows Parental Controls',
	451:'Unavailable For Legal Reasons', 494:'Request Header Too Large',
	495:'Cert Error', 496:'No Cert', 497:'HTTP to HTTPS',
	499:'Client Closed Request', 500:'Internal Server Error',
	501:'Not Implemented', 502:'Bad Gateway', 503:'Service Unavailable',
	504:'Gateway Timeout', 505:'HTTP Version Not Supported',
	506:'Variant Also Negotiates', 507:'Insufficient Storage',
	508:'Loop Detected', 509:'Bandwidth Limit Exceeded', 510:'Not Extended',
	511:'Network Authentication Required', 598:'Network read timeout error',
	599:'Network connect timeout error',
}

def format_status(code):
	return '%i %s' % (code,STATUS_MESSAGES[code])

class URI(object):
	def __init__(self, uri=None, scheme='', host='', path=None, query=None, anchor=''):
		if uri:
			self.scheme, self.host, self.path, _, self.query, self.anchor = urlparse.urlparse(uri)
		self.scheme = scheme or self.scheme
		self.host = host or self.host
		self.path = path or self.path or ['']
		if isinstance(self.path, basestring):
			self.path = self.path.split('/')
		self.query = query or self.query or {}
		self.anchor = anchor or self.anchor

	@classmethod
	def from_env(cls, env):
		return cls(wsgiref.util.request_uri(env))

	def __str__(self):
		result = ''
		if self.scheme or self.host:
			result += '%s://%s' % (self.scheme or 'http', self.host or 'localhost')
		result += '/'.join(self.path or (''))
		if self.query:
			result += '?'+'&'.join('%s=%s'%i for i in self.query.iteritems())
		if self.anchor:
			result += '#' + self.anchor
		return result

	def __repr__(self):
		return `str(self)`

class Request(container):
	"""An object representing the request's environment.

	"""
	def __init__(self, environment):
		self.env = container(environment)
		self.method = self.env.REQUEST_METHOD
		self.uri = URI(wsgiref.util.request_uri(self.env))
		self.args = tuple(self.uri.path[1:].split('/'))
		self.get_vars = dict(urlparse.parse_qsl(self.env.QUERY_STRING, True))
		if self.method == 'GET':
			self.vars = self.get_vars
		elif self.method == 'POST':
			self.vars = self.post_vars
		self.server = container(
			name = self.env.SERVER_NAME,
			port = self.env.SERVER_PORT,
			software = self.env.SERVER_SOFTWARE,
			protocol = self.env.SERVER_PROTOCOL,
		)
		self.cookies = dict((m.key, m.value) for m in Cookie.SimpleCookie(self.env.HTTP_COOKIE or '').values())
		self.wsgi = container((k[5:],self.env.pop(k)) for k,v in self.env.items() if k.startswith('wsgi.'))

def _header(name, decode=lambda x:x, encode=str):
	return property(
		lambda self:decode(self.headers[name]),
		lambda self,new:self.headers.__setitem__(name, encode(new)),
	)

class Response(object):
	def __init__(self):
		self.code = 200
		self.headers = wsgiref.headers.Headers([('Content-type', 'text/html')])
		self.view = None

	def set_cookie(self, name, value, **attr):
		m = Cookie.Morsel()
		m.set(name, value, str(value))
		m.update(attr)
		self.headers['Set-Cookie'] = m.OutputString()

	content_type = _header('Content-Type')
	content_length = _header('Content-Length')

	@staticmethod
	def StreamObj(obj, blksize=8192):
		return wsgiref.util.FileWrapper(obj, blksize)

	@staticmethod
	def StreamPath(path, blksize=8192):
		return wsgiref.util.FileWrapper(open(path, 'rb'), blksize)

class View(object):
	def __init__(self, text):
		self.text = text

	def render(self, vars):
		return self.text % vars

class BaseRouter(object):
	r"""Base class for routing of web requests

	Silk routers handle the following cases:
	* The handler is called and returns normally, generating a response with
	  status code '200 OK' and delivering the returned content
	* The handler is called and returns None. This generates a 404 response
	  which is processed as an HTTP exception, described below
	* The handler raises an HTTP exception. The response has the status code
	  specified in the exception. If the status code is...
	  * 303: A location header is set to redirect the user's browser properly
	  * all others: The response content is set to a dictionary containing
	    the exception's information and rendered through self.error_view
	* The handler raises a normal exception. The router calls self.report_error,
	  ignoring any exceptions and responds with status code 500 and the string
	  contained in self.unhandled_error
	  
	"""
	RequestClass = Request
	ResponseClass = Response

	unhandled_error = "The server has encountered a problem and can't recover. Please try again later."
	error_view = View("Error: %(status)s %(message)s")

	def __init__(self, target=None):
		if target:
			self.handler = target

	def handler(self, request, response):
		raise NotImplementedError

	def report_error(self, (exc, obj, tb), request, response):
		traceback.print_exception(exc, obj, tb)

	def receive_upload(self, infile, length):
		raise NotImplementedError

	def process(self, request, response):
		try:
			response.content = self.handler(request, response)
			if response.content is None:
				raise HTTP(404, request.path)
			return response.view
		except HTTP, e:
			response.code = e.code
			if e.code == 303:
				response.headers['Location'] = e.message
				response.content = []
			else:
				response.content = {'code':e.code, 'status':format_status(e.code), 'message':e.message}
				return self.error_view
		except:
			try:
				self.report_error(sys.exc_info(), request, response)
			except:
				pass
			response.code = 500
			response.content = self.unhandled_error or ''

	def render(self, view, response):
		if isinstance(response.content, basestring):
			return [response.content]
		elif isinstance(response.content, collections.Mapping):
			return [view.render(response.content)]
		elif isinstance(response.content, collections.Iterable):
			return response.content
	
	def wsgi(self):
		global application
		def wsgi_handler(environment, start_response):
			request, response = self.RequestClass(environment), self.ResponseClass()
			content = self.render(self.process(request, response), response)
			start_response(format_status(response.code), response.headers.items())
			return content
		application = wsgi_handler
		return wsgi_handler

	def test_serve(self, host='', port=8000):
		from wsgiref.simple_server import make_server
		httpd = make_server(host, port, self.wsgi())
		try:
			httpd.serve_forever()
		except KeyboardInterrupt:
			exit(0)

	def cgi(self):
		raise NotImplementedError

	def fcgi(self):
		raise NotImplementedError

	def mod_python(self):
		raise NotImplementedError

	def scgi(self):
		raise NotImplementedError

class PathRouter(BaseRouter):
	def __init__(self):
		self.handlers = {}

	def __call__(self, *elements):
		def f(handler):
			self.handlers[elements] = handler
			handler.url = URI()
			return handler
		return f

	def handler(self, request, response):
		elements, args, shift = request.args, (), True
		while shift:
			if elements in self.handlers:
				request.args = args
				return self.handlers[elements](request, response)
			shift = elements[-1:]
			elements = elements[:-1]
			args = shift + args

	def __setitem__(self, key, value):
		if not isinstance(key, tuple):
			key = (key,)
		self.handlers[key] = value

	def __getitem__(self, key):
		return self.handlers[key]

	def __delitem__(self, key):
		del self.handlers[key]

class Document(object):
	def __init__(self, contents, mimetype='text/html'):
		self.contents = contents
		self.mimetype = mimetype

	def __call__(self, request, response):
		if not request.args:
			response.content_type = self.mimetype
			response.content_length = len(self.contents)
			return self.contents

	@classmethod
	def Icon(cls, contents):
		return cls(contents, mimetype='image/ico')

	@classmethod
	def Plain(cls, contents):
		return cls(contents, mimetype='text/plain')

class B64Document(Document):
	def __init__(self, contents, mimetype='text/html'):
		Document.__init__(self, base64.b64decode(contents), mimetype=mimetype)

if __name__=='__main__':
	from silk.webdoc.html import FORM, INPUT, P
	
	router = PathRouter()

	router['favicon.ico'] = B64Document.Icon('AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAC/AAAAvgAAALMAAAA+TExMBgAAAABubm5AAAAAcQAAAHAAAABnAAAAVwAAAC5MTEwU8fHxAQAAAAAAAAAAAAAATgAAAD4AAAArAAAAP0xMTDPx8fEEbm5uKSsrKz3U1NQMkZGRAQAAAAoAAABbTExMW/Hx8QcAAAAAAAAAAAAAAAAAAAAA8fHxBkxMTE1MTExN8fHxBgAAAAAAAAAAAAAAAJGRkR0AAABEAAAAT0xMTDvx8fEEAAAAAAAAAAAAAAAAAAAAAPHx8QlMTExxTExMcfHx8QkAAAAA1NTUDCsrKzgAAABGDg4ORLOzsxUAAAAAAAAAAAAAAAAAAAAAAAAAAJGRkQQAAAASAAAAf0xMTHzx8fEJAAAAANTU1BYrKytrAAAASg4ODgEAAAAAs7OzEA4ODjORkZEXAAAAAAAAAACRkZELAAAAIgAAAIpMTEyD8fHxCgAAAADU1NQIKysrKAAAAEkAAABqAAAAWAAAAFgAAABqkZGRLgAAAAAAAAAAkZGREQAAADAAAACVTExMifHx8QoAAAAA1NTUBSsrKxZubm4P8fHxAUxMTBJMTEwS8fHxAQAAAAAAAAAAAAAAAJGRkRgAAABAAAAAn0xMTI/x8fELbm5uCQAAACwAAACebm5uavHx8QlMTEx6AAAAfQAAABaRkZEGAAAAAAAAAACRkZEZAAAAQwAAAJ5MTEyM8fHxC25ubiAAAABEAAAAcAAAAFwAAAA6AAAAgQAAAIYAAABIkZGRHQAAAAAAAAAAkZGRFgAAADoAAACSTExMg/Hx8Qpubm44AAAAXQAAAEYAAABBAAAARwAAAIEAAACBAAAASpGRkR4AAAAAAAAAAJGRkRIAAAAxAAAAhUxMTHnx8fEJbm5uUAAAAHgAAAAnAAAAEAAAABAAAAAzAAAANAAAABIAAAAmAAAAOAAAAACRkZEOAAAAKAAAAHlMTExv8fHxCG5ublgrKyuB1NTUGgAAAAAAAAAAAAAAAAAAAAAAAAAAbm5uKgAAAEoAAAAAkZGRCQAAAB0AAABsAAAAbwAAACYAAABLKysrWtTU1BIAAAAAAAAAAAAAAAAAAAAAAAAAAG5ubjoAAABmAAAAAAAAAADx8fEGTExMUkxMTFLx8fEGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA8fHxBUxMTEYAAABXAAAAOwAAADArKysi1NTUBwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPHx8QRMTEw2AAAAeQAAANoAAACUKysrSdTU1A8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH/8AAP//AAD//wAA//8AAP//AADn/wAA5/8AAOd/AADn5wAA5+cAAO//AAD+/wAA//8AAP//AAD//wAA+f8AAA==')

	@router()
	def unmatched(request, response):
		response.content_type = 'text/plain'
		response.set_cookie('name', 'value')
		response.set_cookie('name2', 'value2')
		r = dict(request)
		env = r.pop('env')
		return 'Hello World\n%r\n%r' % (r,env)

	@router('')
	def index(request, response):
		return 'Hello World\n%r' % (request.args,)

	@router('abc')
	def abc(request, response):
		return '123'

	@router('abc', '123')
	def abc123(request, response):
		return 'MJ!'

	@router('upload')
	def upload(request, response):
		r = dict(request)
		env = r.pop('env')
		if request.method == 'POST' and request.env.CONTENT_LENGTH:
			data = request.wsgi.input.read(int(request.env.CONTENT_LENGTH))
		else:
			data = ''
		return ''.join(map(str,[
			FORM(INPUT(name='upload',type='file'),INPUT(type='submit'),method='post', enctype='multipart/form-data'),
			P(`r`), P(env)] + [P(repr(x)) for x in data.split('\n')]))

	scriptname = sys.argv[0].rpartition('/')[2]
	if scriptname == 'wsgi.py':
		application = router.wsgi()
	elif scriptname == 'cgi.py':
		router.cgi()
	else:
		router.test_serve()
