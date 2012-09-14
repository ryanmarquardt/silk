r"""

Applications are passed two arguments: one Request object and one Response object
"""

from silk import *

import Cookie
import wsgiref.util
import urlparse

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
	if code == 200:
		return '200 OK'
	else:
		raise NotImplementedError

class uri(str):
	def __new__(cls, env):
		self = str.__new__(cls, wsgiref.util.request_uri(env))
		self.scheme, self.host, self.path, _, self.query, self.anchor = urlparse.urlparse(self)
		#self.scheme = wsgiref.util.guess_scheme(env)
		#self.host = env.HTTP_HOST or env.SERVER_NAME
		return self

	def __repr__(self):
		return `self.__dict__`

class Request(container):
	def __init__(self, environment):
		self.env = container(environment)
		self.method = self.env.REQUEST_METHOD
		self.uri = uri(self.env)
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

	@property
	def content_type(self):
		return self.headers['Content-type']
	@content_type.setter
	def content_type(self, new):
		self.headers['Content-type'] = new

	@staticmethod
	def StreamObj(obj, blksize=8192):
		return wsgiref.util.FileWrapper(obj, blksize)

	@staticmethod
	def StreamPath(path, blksize=8192):
		return wsgiref.util.FileWrapper(open(path, 'rb'), blksize)
