#!/usr/bin/env python

import silk.webreq
import imp
import importlib
import os.path
import sys
import inspect

imported = dict()

def load(name=None, path=None):
	try:
		return reload(imported[name or path])
	except ImportError:
		pass
	except KeyError:
		if path:
			working = os.path.join(basedir, path)
			if name is None:
				base = os.path.relpath(working, basedir)
				if base.startswith('..'):
					raise ImportError("Must give name and path for modules outside of the app's directory")
				name = base.rpartition('.py')[0]
				if '.' in name:
					raise ImportError("Cannot import from paths with '.' in them")
				name = name.replace('/', '.')
				if name.endswith('.__init__'):
					name = name[:-len('.__init__')]
			imported[name] = imp.load_source(name, working)
		elif name:
			imported[name] = importlib.import_module(name)
		return imported[name]

include = execfile

class _Router(silk.webreq.BaseRouter):
	def handler(self, _request, _response):
		self.route = ()
		self.subhandler = None
		global request, response
		request = _request
		request.script_name = self.name
		response = _response
		load(self.modname, self.name)
		return self.subhandler()

_Router = _Router()

def Router(*path):
	def decorator(handler):
		return handler
	if len(request.args) >= len(path):
		for i,e in enumerate(path):
			if request.args[i] != e:
				break
		else:
			def decorator(handler):
				handler_nargs = len(inspect.getargspec(handler).args)
				if handler_nargs == 0:
					if len(request.args) == len(path):
						_Router.subhandler = lambda:handler()
						_Router.route = path
				elif handler_nargs == 1:
					if not _Router.route or len(path) > len(_Router.route):
						_Router.subhandler = lambda:handler(request.args[len(path):])
						_Router.route = path
				else:
					raise TypeError("Routers must accept zero or one arguments")
				return handler
	return decorator

def set_app(app):
	global basedir
	basedir, filename = os.path.split(app)
	sys.path.append(basedir)
	_Router.modname = os.path.splitext(filename)[0]
	_Router.name = app

__all__ = ['request', 'response', 'Router', 'include']
