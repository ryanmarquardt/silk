#!/usr/bin/env python

from distutils.core import setup

setup(
	name='silk',
	version='0.0.1',
	author='Ryan Marquardt',
	author_email='ryan@integralws.com',
	url='http://projects.integralws.com/webdoc',
	description='Tools for WSGI applications',
	packages=[
		'silk',
		'silk.webdoc',
		'silk.webdoc.html',
		'silk.webdb',
		'silk.webdb.drivers',
	],
	license='Simplified BSD License',
)
