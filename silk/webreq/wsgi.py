
from silk import *
from silk.webreq import Request as BaseRequest, Response as BaseResponse, HTTP, format_status

import base64
import collections
import sys
import traceback
import wsgiref.util
import wsgiref.headers

class Request(BaseRequest):
	"""An object representing the request's environment.

	"""
	def __init__(self, environment):
		BaseRequest.__init__(self, environment)
		self.wsgi = container((k[5:],self.env.pop(k)) for k,v in self.env.items() if k.startswith('wsgi.'))

class Response(BaseResponse): pass

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
	
	def wsgi(self, environment, start_response):
		request, response = self.RequestClass(environment), self.ResponseClass()
		view = self.process(request, response)
		start_response(format_status(response.code), response.headers.items())
		return self.render(view, response)

class PathRouter(BaseRouter):
	def __init__(self):
		self.handlers = {}

	def __call__(self, *elements):
		def f(handler):
			self.handlers[elements] = handler
			return handler
		return f

	def handler(self, request, response):
		elements = tuple(request.uri.path[1:].split('/')) + (None,)
		while elements:
			elements = elements[:-1]
			if elements in self.handlers:
				return self.handlers[elements](request, response)

	def __setitem__(self, key, value):
		if not isinstance(key, tuple):
			key = (key,)
		self.handlers[key] = value

	def __getitem__(self, key):
		return self.handlers[key]

	def __delitem__(self, key):
		del self.handlers[key]

def serve(host, port, router=BaseRouter):
	from wsgiref.simple_server import make_server
	httpd = make_server(host, port, router)
	httpd.serve_forever()

class Document(object):
	def __init__(self, contents, mimetype='text/html'):
		self.contents = contents
		self.mimetype = mimetype

	def __call__(self, request, response):
		if not request.args:
			response.content_type = self.mimetype
			
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
	router = PathRouter()
	router.RequestClass = Request
	router.ResponseClass = Response

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

	application = router.wsgi

	serve('', 8000, application)
