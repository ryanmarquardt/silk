#Sample file, producing web2py's standard layout

from webdoc import *
from webdoc.html import *


doc = HTMLDoc(no_js=True, _lang='en', conditional=True)
doc.include(TITLE('web2py Web Framework'))
doc.include('/examples/static/js/modernizr-1.7.min.js')
doc.include(META.http_equiv("X-UA-Compatible", "IE=edge"))
doc.include(META.value('google-site-verification'))
doc.include(META.value('viewport', 'width=device-width, initial-scale=1.0, user-scalable=yes'))
doc.include('/examples/static/favicon.ico')
doc.include('/examples/static/favicon.png', rel='apple-touch-icon')
doc.include('/examples/static/js/modernizr.custom.js')
doc.include(Javascript('    var w2p_ajax_confirm_message = "Are you sure you want to delete this object?";\n    var w2p_ajax_date_format = "%Y-%m-%d";\n    var w2p_ajax_datetime_format = "%Y-%m-%d %H:%M:%S";',type='text/javascript'))
for name in ['js/jquery.js', 'css/calendar.css', 'js/calendar.js', 'js/web2py.js',
             'css/skeleton.css', 'css/web2py.css', 'css/examples.css',
             'js/superfish.js', 'css/superfish.css']:
	doc.include('/examples/static/'+name)
doc.include(Javascript("jQuery(function(){jQuery('.sf-menu').superfish();});"))


for depth, element in doc.walk():
	if isinstance(element, Node):
		print '  '*depth, element.name, element.attributes
	else:
		print '  '*depth, `element`

print

print doc
