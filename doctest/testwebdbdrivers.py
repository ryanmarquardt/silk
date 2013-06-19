#!/usr/bin/env python
import doctest

import silk.webdb
from silk.webdb import *

fdoc = '\n'.join(silk.webdb.__doc__.split('\n')[8:])
fdoc = fdoc.replace('%','%%')
fdoc = fdoc.replace('DB()','DB.connect(%(conn)s, debug=True)')
for driver in drivers.__all__:
	conn = ','.join(map(repr,(driver,)+getattr(getattr(drivers,driver),driver).test_args))
	o = type('',(object,),{'__doc__':fdoc%dict(conn=conn)})
	doctest.run_docstring_examples(o, globals(), name=__file__+'(%s)'%driver)

#If tests fail for mysql, run the following SQL:
#  CREATE DATABASE silk_test;
#  GRANT ALL PRIVILEGES ON SILK_TEST.* TO silk_test@localhost;
