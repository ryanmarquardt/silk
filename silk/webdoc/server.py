
from html.tags import *

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

class attrdict(dict):__getattr__,__setattr__,__delattr__ = dict.get,dict.__setitem__,dict.__delitem__

#class Handler(BaseHTTPRequestHandler):
	#def parse_multipart_form_data(self, callback, chunk_size=4096):
		#if self.headers['Content-Type'] == 'multipart/form-data':
			#data = self.rfile.read(int(self.headers['Content-Length']))
			#return dict(map(urllib.unquote_plus,line.split('=',1)) for line in data.split('&') if line)
		#elif self.headers['Content-Type'].startswith('multipart/form-data; boundary='):
			#boundary = self.headers['Content-Type'][30:]
			#print	`boundary`
			#data = self.rfile.read(int(self.headers['Content-Length']))
			#sections = data.split(boundary)
			#print `sections`
			#result = {}
			#for section in sections[1:]:
				#if section[:2] == '\r\n':
					#headers,section = section[2:].split('\r\n\r\n',1)
					#section = section[:-4]
					#headers = dict(line.split(': ',1) for line in headers.split('\r\n'))
					#print `headers`
					#print `section`
					#cds = dict((word.split('=',1)[0],word.split('=',1)[1][1:-1]) for word in headers['Content-Disposition'].split('; ')[1:])
					#if 'filename' in cds:
						#result[cds['name']] = dict(file=callback(headers, [section]), filename=cds['filename'])
					#else:
						#result[cds['name']] = section
			#return result

	#def redirect(self, path):
		#self.send_response(303)
		#self.send_header('Location', path)
		#self.end_headers()

	#def send(self, data, content_type=None):
		#if hasattr(data,'__iter__'):
			#data = ''.join(map(str,data))
		#self.send_response(200)
		#if content_type:
			#self.send_header('Content-Type', content_type)
		#self.end_headers()
		#self.wfile.write(data)

	#def do_GET(self):
		#request = Request(self.headers)
		#self.router(request)
		#if self.path == '/':
			#self.send()
		#elif self.path == '/my.css':
			#self.send('form{display:inline;}', 'text/css')
		#elif self.path == '/favicon.ico':
			#self.send(FAVICON)
		#else:
			#self.send_error(404, self.path + ' not found')

	#def do_POST(self):
		#print self.headers
		#data = self.parse_multipart_form_data(sample_upload_callback)
		#print data
		#self.redirect('/')

class HTTP(Exception):
	def __init__(self, error_code, message, **headers):
		Exception.__init__(self)
		self.message = message
		self.headers = headers
		self.code = error_code

for name,code in dict(
	#Names and codes from http://en.wikipedia.org/wiki/List_of_HTTP_status_codes
	#retrieved 1/20/2012
	Continue = 100,
	SwitchingProtocols = 101,
	Processing = 102,
	Checkpoint = 103,
	OK = 200,
	Created = 201,
	Accepted = 202,
	NonAuthoritativeInformation = 203,
	NoContent = 204,
	ResetContent = 205,
	PartialContent = 206,
	MultiStatus = 207,
	AlreadyReported = 208,
	IMUsed = 226,
	MultipleChoices = 300,
	MovedPermanently = 301,
	Found = 302,
	SeeOther = 303,
	NotModified = 304,
	UseProxy = 305,
	SwitchProxy = 306,
	TemporaryRedirect = 307,
	ResumeIncomplete = 308,
	BadRequest = 400,
	Unauthorized = 401,
	PaymentRequired = 402,
	Forbidden = 403,
	NotFound = 404,
	MethodNotAllowed = 405,
	NotAcceptable = 406,
	ProxyAuthenticationRequired = 407,
	RequestTimeout = 408,
	Conflict = 409,
	Gone = 410,
	LengthRequired = 411,
	PreconditionFailed = 412,
	RequestEntityTooLarge = 413,
	RequestURITooLong = 414,
	UnsupportedMediaType = 415,
	RequestedRangeNotSatisfiable = 416,
	ExpectationFailed = 417,
	ImATeapot = 418,
	UnprocessableEntity = 422,
	Locked = 423,
	FailedDependency = 424,
	UnorderedCollection = 425,
	UpgradeRequired = 426,
	PreconditionRequired = 428,
	TooManyRequests = 429,
	RequestHeaderFieldsTooLarge = 431,
	NoResponse = 444,
	RetryWith = 449,
	BlockedByWindowsParentalControls = 450,
	ClientClosedRequest = 499,
	InternalServerError = 500,
	NotImplemented = 501,
	BadGateway = 502,
	ServiceUnavailable = 503,
	GatewayTimeout = 504,
	HTTPVersionNotSupported = 505,
	VariantAlsoNegotiates = 506,
	InsufficientStorage = 507,
	LoopDetected = 508,
	BandwidthLimitExceeded = 509,
	NotExtended = 510,
	NetworkAuthenticationRequired = 511,
	NetworkReadTimeoutError = 598,
	NetworkConnectTimeoutError = 599,
).items():
	exec '''class %(name)s(HTTP):\n def __init__(self, *args, **kwargs): HTTP.__init__(self, %(code)s, %(name)s, *args, **kwargs)''' % {'name':name,'code':code}
	setattr(HTTP,name,eval(name))

def Redirect(path):
	raise HTTP(303, '', Location=path)

class Request(attrdict):
	GET = 'GET'
	POST = 'POST'

class Response(attrdict): pass

class Handler(BaseHTTPRequestHandler):
	def parse_headers(self):
		return (
			self.client_address,
			self.path
		)
	
	def do_GET(self):
		request = Request(
			mode = Request.GET,
			path = self.path,
		)
		response = Response(
			code = 200,
			headers = attrdict(),
		)
		self.process(request, response)

	def do_POST(self):
		request = Request(
			mode = Request.POST,
			path = self.path
		)
		response = Response(
			code = 303,
			headers = attrdict(
				Location = self.path,
			),
		)
		self.process(request, response)

	def process(self, request, response):
		try:
			try:
				data = self.server.router(request, response)
			except Exception, e:
				print e
				if isinstance(e, HTTP):
					raise
				else:
					raise HTTP.InternalServerError
		except HTTP, e:
			response.code = e.code
			response.headers = e.headers
			data = self.server.router.error % vars(e)
		self.send_response(response.code)
		for item in response.headers.items():
			if hasattr(item[1],'__iter__'):
				item[1] = '; '.join(item[1])
			self.send_header(*item)
		self.end_headers()
		try:
			if hasattr(data, 'xml'):
				self.wfile.write(data.xml())
			elif hasattr(data, 'render'):
				self.wfile.write(data.render())
			elif isinstance(data, basestring):
				self.wfile.write(data)
		except Exception, e:
			print `e`
			print data



class Router(object):
	error = HTMLDoc(H1('Error %(code)s: %(message)s'))
	error = error.xml()
	def __call__(self, request, response):
		print 'Router.__call__', request, response
		if request.mode == Request.GET:
			return self.GET(request, response)
		elif request.mode == Request.POST:
			return self.POST(request, response)
		else:
			raise HTTP.InternalServerError

class Server(HTTPServer):
	def __init__(self, address, router):
		self.router = router()
		HTTPServer.__init__(self, address, Handler)
