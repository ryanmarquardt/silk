
from silk import *
from silk.webreq import Request, Response, HTTP, format_status

import collections
import sys
import traceback
import wsgiref.util
import wsgiref.headers

class WSGIRequest(Request):
	"""An object representing the request's environment.

	"""
	def __init__(self, environment):
		Request.__init__(self, environment)
		self.wsgi = container((k[5:],self.env.pop(k)) for k,v in self.env.items() if k.startswith('wsgi.'))

class WSGIResponse(Response):
	@staticmethod
	def Stream(filelike, blocksize=8192):
		return wsgiref.util.FileWrapper(filelike, blocksize)

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
	
	def __call__(self, environment, start_response):
		request, response = self.RequestClass(environment), self.ResponseClass()
		view = self.process(request, response)
		start_response(format_status(response.code), response.headers.items())
		return self.render(view, response)

class PathRouter(BaseRouter):
	def __init__(self):
		self.handlers = {}

	def routes(self, *elements):
		def f(handler):
			self.handlers[elements] = handler
			return handler
		return f

	def handler(self, request, response):
		elements = tuple(request.uri.path[1:].split('/'))
		if elements in self.handlers:
			return self.handlers[elements](request, response)
		while elements:
			elements = elements[:-1]
			if elements in self.handlers:
				return self.handlers[elements](request, response)

def serve(host, port, router=BaseRouter):
	from wsgiref.simple_server import make_server
	httpd = make_server(host, port, router)
	httpd.serve_forever()

if __name__=='__main__':
	my_router = PathRouter()
	my_router.RequestClass = WSGIRequest
	my_router.ResponseClass = WSGIResponse
	routes = my_router.routes

	@routes()
	def unmatched(request, response):
		response.content_type = 'text/plain'
		response.headers['Set-Cookie'] = 'name=value'
		response.headers['Set-Cookie'] = 'name2="value2 3"'
		r = dict(request)
		env = r.pop('env')
		return 'Hello World\n%r\n%r' % (r,env)

	@routes('')
	def index(request, response):
		return 'Hello World'

	@routes('abc')
	def abc(request, response):
		return '123'

	serve('', 8000, my_router)
