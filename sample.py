#Sample file, producing web2py's standard layout

from webdoc import *
from webdoc.html import *
import webdoc.css

def AddToAny():
	return [
		DIV(
			A('Share', _class='a2a_dd', _href='http://www.addtoany.com/share_save'),
		_style='float:right;padding-top:6px', _class=['a2a_kit','a2a_default_style']
		),
		Javascript(_src='http://static.addtoany.com/menu/page.js'),
	]

doc = HTMLDoc(
	no_js=True,
	lang='en',
	conditional=True,
	title='web2py Web Framework',
	includes=[
		'/examples/static/js/modernizr-1.7.min.js',
		CONDITIONAL_COMMENT('IE',META.http_equiv("X-UA-Compatible", "IE=edge")),
		META.value('google-site-verification'),
		META.value('viewport', 'width=device-width, initial-scale=1.0, user-scalable=yes'),
		'/examples/static/favicon.ico',
		'/examples/static/js/modernizr.custom.js',
		Javascript('    var w2p_ajax_confirm_message = "Are you sure you want to delete this object?";\n    var w2p_ajax_date_format = "%Y-%m-%d";\n    var w2p_ajax_datetime_format = "%Y-%m-%d %H:%M:%S";',type='text/javascript'),
		]+['/examples/static/'+name for name in ['js/jquery.js', 'css/calendar.css',
		'js/calendar.js', 'js/web2py.js', 'css/skeleton.css', 'css/web2py.css',
		'css/examples.css', 'js/superfish.js', 'css/superfish.css']]+[
		Javascript("jQuery(function(){jQuery('.sf-menu').superfish();});"),
	]
)
doc.include('/examples/static/favicon.png', rel='apple-touch-icon')
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
						UL([LI(A(text,_href='/examples/default/'+link)) for text,link in [
							('Home','index'), ('About','what'), ('Download','download'),
							('Docs & Resources','documentation'), ('Support','support'), ('Contributors','who'),
						]], _class='sf-menu'),
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
							A('DOWNLOAD NOW',_class='button', href='/examples/default/download',style=css.WIDTH(pct=90)), ' ',
							A('ONLINE DEMO',_class='button', href='http://web2py.com/demo_admin',style=css.WIDTH(pct=90)), ' ',
							A('SITES POWERED BY WEB2PY',_class='button', href='http://web2py.com/poweredby',style=css.WIDTH(pct=90)),
						_class=['one-third','column'], _style='text-align:center'),
					_class=['one-third','column','omega']),
				_class=['sixteen','columns']),
			_class=['container','mainbody']),
			DIV(
				DIV(
					DIV(
						H3(A('BATTERIES INCLUDED',href='/examples/default/what')),
						P('Everything you need in one package including fast multi-threaded web server, SQL database and web-based interface. No third party dependencies but works with ',A('third party tools',href='/examples/default/what'),'.'),
					_class=['one-third','column','alpha']),
					DIV(
						H3(A('WEB-BASED IDE',href='http://web2py.com/demo_admin')),
						P('Create, modify, deploy and manage application from anywhere using your browser. One web2py instance can run multiple web sites using different databases. Try the ',A('interactive demo',href='http://web2py.com/demo_admin'),'.'),
					_class=['one-third','column']),
					DIV(
						H3(A('EXTENSIVE DOCS',href='/examples/default/documentation')),
						P(
							'Start with some ',
							A('quick examples',href='/examples/default/examples'),
							', then read the',
							A('manual',href='http://web2py.com/book',target='_blank'),
							', watch ',
							A('videos',href='http://vimeo.com/album/178500',target='_blank'),
							', and join a ',
							A('user group',href='/examples/default/usergroups'),
							' for discussion. Take advantage of the ',
							A('layouts', href='http://web2py.com/layouts',target='_blank'),
							', ', A('plugins',href='http://dev.s-cubism.com/web2py_plugins',target='_blank'),
							', ', A('appliances',href='http://www.web2py.com/appliances',target='_blank'),
							', and', A('recipes',href='http://web2pyslices.com',target='_blank'), '.',
						),
					_class=['one-third','column','omega']),
				_class=['sixteen','columns']),
			_class=['container','aboutW2P']),
			IMG(_class=['scale-with-grid','centered'],src='/examples/static/images/shadow-bottom.png'),
			DIV(
				DIV(
					DIV(
						EM(P('web2py was the life saver today for me, my blog post: Standalone Usage of web2py',XML('&#x27;'),'s')),
						SPAN(
							A(EM(XML('&mdash;'),'caglartoklu'),href='http://twitter.com/#!/caglartoklu/status/84292131707031553'),
						_class='right'),
					_class=['one-third','column','alpha']),
					DIV(
						EM(P('web2py rules! as a sysadmin I like the no installation and no configuration approach a lot)')),
						SPAN(
							A(EM(XML('&mdash;'),'kjogut'),href='http://twitter.com/#!/jkogut/status/61414554273447936'),
						_class='right'),
					_class=['one-third','column']),
					DIV(
						EM(P('web2py it is. Compatible with everything under the sun and great interfaces to googleappengine')),
						SPAN(
							A(EM(XML('&mdash;'),'comamitc'),href='http://twitter.com/#!/comamitc/status/51744719071477760'),
						_class='right'),
					_class=['one-third','column','omega']),
				_class=['sixteen','columns']),
			_class=['container','userQuotes']),
		_class='main'),
		DIV(_class='push'),
	_class='wrapper'),
	DIV(
		DIV(
			DIV(
				DIV(
					'\nCopyright ',XML('&#169;'),' 2011\n - User communities in ',
					A('English',href='https://groups.google.com/forum/?fromgroups#!forum/web2py',target='_blank'), ', ',
					A('French',href='https://groups.google.com/forum/?fromgroups#!forum/web2py-fr',target='_blank'), ', ',
					A('Japanese',href='https://groups.google.com/forum/?fromgroups#!forum/web2py-japan',target='_blank'), ', ',
					A('Portuguese',href='https://groups.google.com/forum/?fromgroups#!forum/web2py-users-brazil',target='_blank'), ', and ',
					A('Spanish',href='https://groups.google.com/forum/?fromgroups#!forum/web2py-usuarios',target='_blank'), '.',
					DIV(
						A(IMG(style=css.PADDING_BOTTOM(0),src='/examples/static/images/poweredby.png'),href='https://www.web2py.com/',style=[css.FLOAT('left'),css.PADDING_RIGHT(px=6)]),
					#_style=css.FLOAT('right')),
					_style=css.css(float='right')),
				_class='footer-content'),
			_class=['sixteen','columns']),
		_class=['container','header']),
	_class='footer'),
	CONDITIONAL_COMMENT('lt IE 7',
		Javascript(src='/examples/static/js/dd_belatedpng.js'),
		Javascript("DD_belatedPNG.fix('img, .png_bg');"),
	),
)



for depth, element in doc.walk():
	if isinstance(element, Node):
		print '  '*depth, element.name, element.attributes
	else:
		print '  '*depth, `element`

#print

#print doc
