#Sample file, producing web2py's standard layout

from webdoc import *
from webdoc.html import *
import webdoc.css

def AddToAny():
	return CAT(
		DIV(
			A('Share', _class='a2a_dd', _href='http://www.addtoany.com/share_save'),
		_style='float:right;padding-top:6px', _class=['a2a_kit','a2a_default_style']
		),
		Javascript(_src='http://static.addtoany.com/menu/page.js'),
	)

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
doc.body = Body(
	DIV(
		DIV(_class='flash'),
		DIV(
			DIV(
				DIV(
					IMG(_src='/examples/static/images/web2py_logo.png', _class='logo', _alt='web2py logo'),
					H5(),
				_class=['sixteen', 'columns']),
				DIV(
					DIV(
						UL((LI(A(text,_href='/examples/default/'+link)) for text,link in [
							('Home','index'), ('About','what'), ('Download','download'),
							('Docs & Resources','documentation'), ('Support','support'), ('Contributors','who'),
					]), _class='sf-menu'),
					AddToAny(),
					_id='menu', _class='clearfix'),
				_class=['sixteen','columns','statusbar']),
			_class='container'),
			DIV(
				A("InfoWorld's 2012 Technology of the Year Award Winner",_href='http://www.infoworld.com/slideshow/24605/infoworlds-2012-technology-of-the-year-award-winners-183313#slide23', _target='_blank'),
			_class=['sixteen','columns','announce']),
		_class='header'),
		DIV(
			DIV(
				DIV(
					DIV(
						TABLE(
							TR(
								TD(A(IMG(_src='/examples/static/images/book-4th.png'),_href='http://web2py.com/book')),
								TD(A(IMG(_src='/examples/static/images/book-recipes.png'),_href='http://link.packtpub.com/SUlnrN')),
								TD(A(IMG(_src='/examples/static/images/videos.png'),_href='http://www.youtube.com/playlist?list=PL5E2E223FE3777851')),
							),
						width=css.Units.Pct(100)),
						H3('WEB2PY', SUP('TM'), 'WEB FRAMEWORK'),
						P('Free open source full-stack framework for rapid development of fast, scalable, ',A('secure',_href='http://www.web2py.com/book/default/chapter/01#security',_target='_blank'),' and portable database-driven web-based applications. Written and programmable in ',A('Python',_href='http://www.python.org',_target='_blank'),'. ',A('LGPLv3 License',_href='http://www.gnu.org/licenses/lgpl.html'),'. Current version: 1.99.7 (2012-03-04 22:12:08) stable'),
					_class=['two-thirds','column','alpha']),
					DIV(
						DIV(
							IMG(_class=['scale-with-grid','centered'], src='/examples/static/images/tag-cloud-color-small.png', width=css.Units.Px(300)),
							BR(),
							A('DOWNLOAD NOW',_class='button', href='/examples/default/download',style=css.Width(pct=90)),
							A('ONLINE DEMO',_class='button', href='http://web2py.com/demo_admin',style=css.Width(pct=90)),
							A('SITES POWERED BY WEB2PY',_class='button', href='http://web2py.com/poweredby',style=css.Width(pct=90)),
						_class=['one-third','column'], _style='text-align:center'),
					_class=['one-third','column','omega']),
				_class=['sixteen','columns']),
			_class=['container','mainbody']),
		_class='main'),
	_class='wrapper'),
)



#for depth, element in doc.walk():
	#if isinstance(element, Node):
		#print '  '*depth, element.name, element.attributes
	#else:
		#print '  '*depth, `element`

#print

print doc
