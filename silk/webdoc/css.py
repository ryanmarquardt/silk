"""Construct css style sheets from abstract structure

>>> print(Block(Selector('div'),
...     Property.new('padding')('0', Units.Px(20), Units.Px(15)),
...     BACKGROUND('transparent'),
...     BORDER(Units.Px(1), 'solid', Colors.Black),
... ))
div { padding: 0 20px 15px; background: transparent; border: 1px solid #000000; }

As a shortcut, selectors can be given as strings, and attributes as dictionaries

>>> a = Block('a', {'color': Colors.Red})
>>> print(a)
a { color: #FF0000; }

Nodes are created from these values, so they can be accessed and manipulated
later.

>>> a.selectors[0]['_state'] = 'hover'
>>> print(a)
a:hover { color: #FF0000; }

Several helper functions and constants exist.

Colors are stored with CamelCase names
>>> Colors.Black
'#000000'
>>> Colors.from_rgb(255,255,255)
'#FFFFFF'

Classes for common properties exist also
>>> print(DISPLAY(None))
display: none;
>>> print(BORDER.WIDTH(px=1))
border-width: 1px;
"""

from .. import *
from .node import *

from functools import partial

def _css(value):
	return 'none' if value is None else str(value)

class CSSNode(Node):
	pass

class Block(CSSNode):
	'''
	
	>>> print(Block('body',
	...   Property.new('background')('white'),
	... ))
	body { background: white; }
	'''
	def __init__(self, selector, *children, **attributes):
		self.selectors = [Selector(a) if not isinstance(a,CSSNode) else a for a in sequence(selector)]
		mychildren = []
		for child in children:
			if isinstance(child, dict):
				mychildren.extend(Property.new(prop)(*sequence(val)) for prop,val in list(child.items()))
			else:
				mychildren.append(child)
		for k,v in list(attributes.items()):
			mychildren.append(Property.new(k.replace('_','-'))(*sequence(v)))
		super(Block, self).__init__(*mychildren)
		
	def __str__(self):
		return '%s { %s }' % (', '.join(map(str,self.selectors)), ' '.join(map(_css,self.children)))
	
class Property(CSSNode):
	'''Class for specifying a css property in a block
	
	>>> print(Property.new('background')('transparent'))
	background: transparent;
	>>> print(Property.new('padding')(0, Units.Px(0), Units.In(15), Units.Px(15)))
	padding: 0 0 15in 15px;
	
	A single keyword provided as a lower-cased unit name is appended to the list
	of values, transformed into a unitted value. Output with more than one
	keyword input is undefined and not recommended. 
	
	>>> print(Property.new('width')(px=100))
	width: 100px;
	>>> print(Property.new('border-left')('solid', 'black', em=1))
	border-left: solid black 1em;
	
	If value is an iterable, all members are transformed and appended to the
	list of children.
	
	>>> print(Property.new('padding')(px=[0,0,25,50]))
	padding: 0 0 25px 50px;
	
	The special keyword 'important' appends '!important' to the list of children
	if it's set to a true value.
	>>> print(Property.new('position')('absolute', important=True))
	position: absolute !important;
	'''
	def __init__(self, *values, **units):
		important = units.pop('important', False)
		values = list(values)
		if units:
			unit = list(units.keys())[0].title()
			if unit[0] == '_':
				unit = unit[1:]
			values.extend(list(map(Units[unit], sequence(list(units.values())[0]))))
		if important:
			values.append('!important')
		super(Property, self).__init__(*values)

	def __str__(self):
		return ' '.join('%s%s: %s;' % (p, self.name, ' '.join(map(_css,self.children))) for p in [''] + (getattr(self,'__prefixes__') or []))

class CSSDoc(CSSNode):
	def __str__(self):
		return '\n'.join(map(str,self.children))

class Selector(CSSNode):
	'''Class for specifying a css element selector
	
	Match elements by type
	
	>>> print(Selector('input'))
	input
	
	Match elements by class
	
	>>> print(Selector(_class='important'))
	.important
	
	Match elements by id
	
	>>> print(Selector('div', _id='content'))
	div#content
	
	Match elements by ancestry
	>>> print(Selector('div', Selector('p')))
	div p
	>>> print(Selector('div', _child=Selector('p')))
	div>p
	
	Match elements with a certain state
	>>> print(Selector('a', _state='hover'))
	a:hover
	
	'''
	def __str__(self):
		result = ''
		if self.children:
			result += self.children[0]
		_class = self.get('_class')
		if _class: result += '.'+_class
		_id = self.get('_id')
		if _id: result += '#'+_id
		_state = self.get('_state')
		if _state: result += ':'+_state
		_child = self.get('_child')
		if _child: result += '>'+str(_child)
		return ' '.join([result] + list(map(str,self.children[1:])))

def Unit(fmt, i, force=False):
	try:
		i = float(i)
	except ValueError:
		return i
	else:
		return fmt%i if i or force else '0'

from functools import partial

Units = container(
	Px = partial(Unit, '%gpx'),
	In = partial(Unit, '%gin'),
	Cm = partial(Unit, '%gcm'),
	Mm = partial(Unit, '%gmm'),
	Em = partial(Unit, '%gem'),
	Ex = partial(Unit, '%gex'),
	Pt = partial(Unit, '%gpt'),
	Pc = partial(Unit, '%gpc'),
	Pct = partial(Unit, '%g%%'),
	S = partial(Unit, '%gs', force=True),
)

def url(path):
	return 'url(%r)'%path

def newp(name, prefixes=None):
	p = Property.new(name, name.upper().replace('-','_'))
	if prefixes:
		p.__prefixes__ = prefixes
	return p

class ANIMATION(Property):
	name = 'animation'
	NAME = newp('animation-name')
	DURATION = newp('animation-duration')
	TIMING_FUNCTION = newp('animation-timing-function')
	DELAY = newp('animation-delay')
	ITERATION_COUNT = newp('animation-interation-count')
	DIRECTION = newp('animation-direction')
	PLAY_STATE = newp('animation-play-state')

class BACKGROUND(Property):
	name = 'background'
	ATTACHMENT = newp('background-attachment')
	COLOR = newp('background-color')
	IMAGE = newp('background-image')
	POSITION = newp('background-position')
	REPEAT = newp('background-repeat')
	CLIP = newp('background-clip')
	ORIGIN = newp('background-origin')
	SIZE = newp('background-size')

class BORDER(Property):
	name = 'border'
	COLOR = newp('border-color')
	STYLE = newp('border-style')
	WIDTH = newp('border-width')
	class TOP(Property):
		name = 'border-top'
		COLOR = newp('border-top-color')
		STYLE = newp('border-top-style')
		WIDTH = newp('border-top-width')
	class RIGHT(Property):
		name = 'border-right'
		COLOR = newp('border-right-color')
		STYLE = newp('border-right-style')
		WIDTH = newp('border-right-width')
	class BOTTOM(Property):
		name = 'border-bottom'
		COLOR = newp('border-bottom-color')
		STYLE = newp('border-bottom-style')
		WIDTH = newp('border-bottom-width')
	class LEFT(Property):
		name = 'border-left'
		COLOR = newp('border-left-color')
		STYLE = newp('border-left-style')
		WIDTH = newp('border-left-width')
	class RADIUS(Property):
		name = 'border-radius'
		__prefixes__ = ['-moz-','-webkit-']
		BOTTOM_LEFT = newp('border-bottom-left-radius')
		BOTTOM_RIGHT = newp('border-bottom-right-radius')
		TOP_LEFT = newp('border-top-left-radius')
		TOP_RIGHT = newp('border-top-right-radius')
	class IMAGE(Property):
		name = 'border-image'
		OUTSET = newp('border-image-outset')
		REPEAT = newp('border-image-repeat')
		SLICE = newp('border-image-slice')
		SOURCE = newp('border-image-source')
		WIDTH = newp('border-image-width')

class OUTLINE(Property):
	name = 'outline'
	COLOR = newp('outline-color')
	STYLE = newp('outline-style')
	WIDTH = newp('outline-width')
	OFFSET = newp('outline-offset')

class BOX_SHADOW(Property):
	name = 'box-shadow'
class OVERFLOW(Property):
	name = 'overflow'
	X = newp('overflow-x')
	Y = newp('overflow-y')
	STYLE = newp('overflow-style')
class ROTATION(Property):
	name = 'rotation'
	POINT = newp('rotation-point')

class OPACITY(Property):
	name = 'opacity'
class WIDTH(Property):
	name = 'width'
class MAX_WIDTH(Property):
	name = 'max-width'
class MIN_WIDTH(Property):
	name = 'min-width'
WIDTH.MAX = MAX_WIDTH
WIDTH.MIN = MIN_WIDTH
class HEIGHT(Property):
	name = 'height'
class MAX_HEIGHT(Property):
	name = 'max-height'
class MIN_HEIGHT(Property):
	name = 'min-height'
HEIGHT.MAX = MAX_HEIGHT
HEIGHT.MIN = MIN_HEIGHT

class BOX(container):
	ALIGN = newp('box-align')
	DIRECTION = newp('box-direction')
	FLEX = newp('box-flex')
	FLEX_GROUP = newp('box-flex-group')
	LINES = newp('box-lines')
	ORDINAL_GROUP = newp('box-ordinal-group')
	ORIENT = newp('box-orient')
	PACK = newp('box-pack')

class FONT(container):
	FACE = newp('font-face')
	FAMILY = newp('font-family')
	SIZE = newp('font-size')
	STYLE = newp('font-style')
	VARIANT = newp('font-variant')
	WEIGHT = newp('font-weight')
	SIZE_ADJUST = newp('font-size-adjust')
	STRETCH = newp('font-stretch')

class CONTENT(Property):
	name = 'content'
class COUNTER(container):
	INCREMENT = newp('counter-increment')
	RESET = newp('counter-reset')
	
class QUOTES(Property):
	name = 'quotes'
class GRID(container):
	COLUMNS = newp('grid-columns')
	ROWS = newp('grid-rows')

class TARGET(Property):
	name = 'target'
	NAME = newp('target-name')
	NEW = newp('target-new')
	POSITION = newp('target-position')

class LIST_STYLE(Property):
	name = 'list-style'
	IMAGE = newp('list-style-image')
	POSITION = newp('list-style-position')
	TYPE = newp('list-style-type')

class MARGIN(Property):
	name = 'margin'
	TOP = newp('margin-top')
	RIGHT = newp('margin-right')
	BOTTOM = newp('margin-bottom')
	LEFT = newp('margin-left')

class COLUMN(container):
	COUNT = newp('column-count')
	FILL = newp('column-fill')
	GAP = newp('column-gap')
	class RULE(Property):
		name = 'column-rule'
		COLOR = newp('column-rule-color')
		STYLE = newp('column-rule-style')
		WIDTH = newp('column-rule-width')
	SPAN = newp('column-span')
	WIDTH = newp('column-width')
class COLUMNS(Property):
	name = 'columns'

class PADDING(Property):
	name = 'padding'
	TOP = newp('padding-top')
	RIGHT = newp('padding-right')
	BOTTOM = newp('padding-bottom')
	LEFT = newp('padding-left')

class TOP(Property):
	name = 'top'
class RIGHT(Property):
	name = 'right'
class BOTTOM(Property):
	name = 'bottom'
class LEFT(Property):
	name = 'left'
class CLEAR(Property):
	name = 'clear'
class CLIP(Property):
	name = 'clip'
class CURSOR(Property):
	name = 'cursor'
class DISPLAY(Property):
	name = 'display'
class FLOAT(Property):
	name = 'float'
class POSITION(Property):
	name = 'position'
class VISIBILITY(Property):
	name = 'visibility'
class Z_INDEX(Property):
	name = 'z-index'

class ORPHANS(Property):
	name = 'orphans'
class PAGE_BREAK(container):
	AFTER = newp('page-break-after')
	BEFORE = newp('page-break-before')
	INSIDE = newp('page-break-inside')
class WIDOWS(Property):
	name = 'widows'

class BORDER_COLLAPSE(Property):
	name = 'border-collapse'
class BORDER_SPACING(Property):
	name = 'border-spacing'
class CAPTION_SIDE(Property):
	name = 'caption-side'
class EMTPY_CELLS(Property):
	name = 'empty-cells'
class TABLE_LAYOUT(Property):
	name = 'table-layout'
	
class COLOR(Property):
	name = 'color'
class DIRECTION(Property):
	name = 'direction'
class LETTER_SPACING(Property):
	name = 'letter-spacing'
class LINE_HEIGHT(Property):
	name = 'line-height'
class TEXT(container):
	ALIGN = newp('text-align')
	DECORATION = newp('text-decoration')
	INDENT = newp('text-indent')
	TRANSFORM = newp('text-transform')
	ALIGN_LAST = newp('text-align-last')
	JUSTIFY = newp('text-justify')
	OUTLINE = newp('text-outline')
	OVERFLOW = newp('text-overflow')
	SHADOW = newp('text-shadow')
	WRAP = newp('text-wrap')
class VERTICAL_ALIGN(Property):
	name = 'vertical-align'
class WHITE_SPACE(Property):
	name = 'white-space'
class WORD_SPACING(Property):
	name = 'word-spacing'
class HANGING_PUNCTUATION(Property):
	name = 'hanging-punctuation'
class PUNCTUATION_TRIM(Property):
	name = 'punctuation-trim'
class WORD_BREAK(Property):
	name = 'word-break'
class WORD_WRAP(Property):
	name = 'word-wrap'

class TRANSFORM(Property):
	name = 'transform'
	ORIGIN = newp('transform-origin')
	STYLE = newp('transform-style')
class PERSPECTIVE(Property):
	name = 'perspective'
	ORIGIN = newp('perspective-origin')
class BACKFACE_VISIBILITY(Property):
	name = 'backface-visibility'
class TRANSITION(Property):
	name = 'transition'
	PROPERTY = newp('transition-property')
	DURATION = newp('transition-duration')
	TIMING_FUNCTION = newp('transition-timing-function')
	DELAY = newp('transition-delay')

class APPEARANCE(Property):
	name = 'appearance'
class BOX_SIZING(Property):
	name = 'box-sizing'
class ICON(Property):
	name = 'icon'
class NAV(container):
	DOWN = newp('nav-down')
	INDEX = newp('nav-index')
	LEFT = newp('nav-left')
	RIGHT = newp('nav-right')
	UP = newp('nav-up')
class RESIZE(Property):
	name = 'resize'

del newp

def css(**attributes):
	return [globals()[name.upper().replace('-','_')](*sequence(value)) for name,value in list(attributes.items())]

Colors = container(
	from_rgb = lambda r,g,b:'#%02X%02X%02X'%(r,g,b),
	AliceBlue = "#F0F8FF",
	AntiqueWhite = "#FAEBD7",
	Aqua = "#00FFFF",
	Aquamarine = "#7FFFD4",
	Azure = "#F0FFFF",
	Beige = "#F5F5DC",
	Bisque = "#FFE4C4",
	Black = "#000000",
	BlanchedAlmond = "#FFEBCD",
	Blue = "#0000FF",
	BlueViolet = "#8A2BE2",
	Brown = "#A52A2A",
	BurlyWood = "#DEB887",
	CadetBlue = "#5F9EA0",
	Chartreuse = "#7FFF00",
	Chocolate = "#D2691E",
	Coral = "#FF7F50",
	CornflowerBlue = "#6495ED",
	Cornsilk = "#FFF8DC",
	Crimson = "#DC143C",
	Cyan = "#00FFFF",
	DarkBlue = "#00008B",
	DarkCyan = "#008B8B",
	DarkGoldenRod = "#B8860B",
	DarkGray = "#A9A9A9",
	DarkGrey = "#A9A9A9",
	DarkGreen = "#006400",
	DarkKhaki = "#BDB76B",
	DarkMagenta = "#8B008B",
	DarkOliveGreen = "#556B2F",
	Darkorange = "#FF8C00",
	DarkOrchid = "#9932CC",
	DarkRed = "#8B0000",
	DarkSalmon = "#E9967A",
	DarkSeaGreen = "#8FBC8F",
	DarkSlateBlue = "#483D8B",
	DarkSlateGray = "#2F4F4F",
	DarkSlateGrey = "#2F4F4F",
	DarkTurquoise = "#00CED1",
	DarkViolet = "#9400D3",
	DeepPink = "#FF1493",
	DeepSkyBlue = "#00BFFF",
	DimGray = "#696969",
	DimGrey = "#696969",
	DodgerBlue = "#1E90FF",
	FireBrick = "#B22222",
	FloralWhite = "#FFFAF0",
	ForestGreen = "#228B22",
	Fuchsia = "#FF00FF",
	Gainsboro = "#DCDCDC",
	GhostWhite = "#F8F8FF",
	Gold = "#FFD700",
	GoldenRod = "#DAA520",
	Gray = "#808080",
	Grey = "#808080",
	Green = "#008000",
	GreenYellow = "#ADFF2F",
	HoneyDew = "#F0FFF0",
	HotPink = "#FF69B4",
	IndianRed = "#CD5C5C",
	Indigo = "#4B0082",
	Ivory = "#FFFFF0",
	Khaki = "#F0E68C",
	Lavender = "#E6E6FA",
	LavenderBlush = "#FFF0F5",
	LawnGreen = "#7CFC00",
	LemonChiffon = "#FFFACD",
	LightBlue = "#ADD8E6",
	LightCoral = "#F08080",
	LightCyan = "#E0FFFF",
	LightGoldenRodYellow = "#FAFAD2",
	LightGray = "#D3D3D3",
	LightGrey = "#D3D3D3",
	LightGreen = "#90EE90",
	LightPink = "#FFB6C1",
	LightSalmon = "#FFA07A",
	LightSeaGreen = "#20B2AA",
	LightSkyBlue = "#87CEFA",
	LightSlateGray = "#778899",
	LightSlateGrey = "#778899",
	LightSteelBlue = "#B0C4DE",
	LightYellow = "#FFFFE0",
	Lime = "#00FF00",
	LimeGreen = "#32CD32",
	Linen = "#FAF0E6",
	Magenta = "#FF00FF",
	Maroon = "#800000",
	MediumAquaMarine = "#66CDAA",
	MediumBlue = "#0000CD",
	MediumOrchid = "#BA55D3",
	MediumPurple = "#9370D8",
	MediumSeaGreen = "#3CB371",
	MediumSlateBlue = "#7B68EE",
	MediumSpringGreen = "#00FA9A",
	MediumTurquoise = "#48D1CC",
	MediumVioletRed = "#C71585",
	MidnightBlue = "#191970",
	MintCream = "#F5FFFA",
	MistyRose = "#FFE4E1",
	Moccasin = "#FFE4B5",
	NavajoWhite = "#FFDEAD",
	Navy = "#000080",
	OldLace = "#FDF5E6",
	Olive = "#808000",
	OliveDrab = "#6B8E23",
	Orange = "#FFA500",
	OrangeRed = "#FF4500",
	Orchid = "#DA70D6",
	PaleGoldenRod = "#EEE8AA",
	PaleGreen = "#98FB98",
	PaleTurquoise = "#AFEEEE",
	PaleVioletRed = "#D87093",
	PapayaWhip = "#FFEFD5",
	PeachPuff = "#FFDAB9",
	Peru = "#CD853F",
	Pink = "#FFC0CB",
	Plum = "#DDA0DD",
	PowderBlue = "#B0E0E6",
	Purple = "#800080",
	Red = "#FF0000",
	RosyBrown = "#BC8F8F",
	RoyalBlue = "#4169E1",
	SaddleBrown = "#8B4513",
	Salmon = "#FA8072",
	SandyBrown = "#F4A460",
	SeaGreen = "#2E8B57",
	SeaShell = "#FFF5EE",
	Sienna = "#A0522D",
	Silver = "#C0C0C0",
	SkyBlue = "#87CEEB",
	SlateBlue = "#6A5ACD",
	SlateGray = "#708090",
	SlateGrey = "#708090",
	Snow = "#FFFAFA",
	SpringGreen = "#00FF7F",
	SteelBlue = "#4682B4",
	Tan = "#D2B48C",
	Teal = "#008080",
	Thistle = "#D8BFD8",
	Tomato = "#FF6347",
	Turquoise = "#40E0D0",
	Violet = "#EE82EE",
	Wheat = "#F5DEB3",
	White = "#FFFFFF",
	WhiteSmoke = "#F5F5F5",
	Yellow = "#FFFF00",
	YellowGreen = "#9ACD32",
)

__all__ = ['ANIMATION', 'APPEARANCE', 'BACKFACE_VISIBILITY', 'BACKGROUND',
'BORDER', 'BORDER_COLLAPSE', 'BORDER_SPACING', 'BOTTOM', 'BOX', 'BOX_SHADOW',
'BOX_SIZING', 'Block', 'CAPTION_SIDE', 'CLEAR', 'CLIP', 'COLOR', 'COLUMN',
'COLUMNS', 'CONTENT', 'COUNTER', 'CSSDoc', 'CSSNode', 'CURSOR', 'Colors',
'DIRECTION', 'DISPLAY', 'EMTPY_CELLS', 'FLOAT', 'FONT', 'GRID',
'HANGING_PUNCTUATION', 'HEIGHT', 'ICON', 'LEFT', 'LETTER_SPACING', 
'LINE_HEIGHT', 'LIST_STYLE', 'MARGIN', 'MAX_HEIGHT', 'MAX_WIDTH', 'MIN_HEIGHT',
'MIN_WIDTH', 'NAV', 'OPACITY', 'ORPHANS', 'OUTLINE', 'OVERFLOW', 'PADDING',
'PAGE_BREAK', 'PERSPECTIVE', 'POSITION', 'PUNCTUATION_TRIM', 'Property',
'QUOTES', 'RESIZE', 'RIGHT', 'ROTATION', 'Selector', 'TABLE_LAYOUT', 'TARGET',
'TEXT', 'TOP', 'TRANSFORM', 'TRANSITION', 'Unit', 'Units', 'VERTICAL_ALIGN',
'VISIBILITY', 'WHITE_SPACE', 'WIDOWS', 'WIDTH', 'WORD_BREAK', 'WORD_SPACING',
'WORD_WRAP', 'Z_INDEX', 'css', 'url']

