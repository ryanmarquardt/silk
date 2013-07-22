#!/usr/bin/env python

import doctest

import silk
doctest.testmod(silk)

import silk.webdoc
doctest.testmod(silk.webdoc)
doctest.testmod(silk.webdoc.node)
doctest.testmod(silk.webdoc.css)
doctest.testmod(silk.webdoc.html)
doctest.testmod(silk.webdoc.html.common)
import silk.webdoc.stencil
doctest.testmod(silk.webdoc.stencil)
import silk.webdoc.html.html4
import silk.webdoc.html.html5
doctest.testmod(silk.webdoc.html.html4)
doctest.testmod(silk.webdoc.html.html5)

import silk.webreq
doctest.testmod(silk.webreq)

import silk.webdb
doctest.testmod(silk.webdb)
doctest.testmod(silk.webdb.drivers)
doctest.testmod(silk.webdb.drivers.base)
