"""Construct css style sheets from abstract structure

>>> print Block(Selector('div'),
...     Property('padding', '0', Units.Px(20), Units.Px(15)),
...     Property('background', 'transparent'),
...     Property('border', Units.Px(1), 'solid', Colors.Black),
... )
div { padding: 0 20px 15px; background: transparent; border: 1px solid #000000; }

As a shortcut, selectors can be given as strings, and attributes as dictionaries

>>> a = Block('a', {'color': Colors.Red})
>>> print a
a { color: #FF0000; }

Nodes are created from these values, so they can be accessed and manipulated
later.

>>> a.name['_state'] = 'hover'
>>> print a
a:hover { color: #FF0000; }

Several helper functions and constants exist.

Colors are stored with CamelCase names
>>> Colors.Black
'#000000'
>>> Colors.from_rgb(255,255,255)
'#FFFFFF'

"""

from common import *
from node import *

from functools import partial

def _css(value):
	return 'none' if value is None else str(value)

__all__ = ['CSSNode']
class CSSNode(Node):
	pass

__all__.append('Block')
class Block(CSSNode, NoAttributesMixin):
	def __init__(self, name=None, *children, **attributes):
		if not isinstance(name, CSSNode): name = Selector(name)
		mychildren = []
		for child in children:
			if isinstance(child, dict):
				mychildren.extend(Property(prop,*sequence(val)) for prop,val in child.items())
			else:
				mychildren.append(child)
		super(Block, self).__init__(name, *mychildren, **attributes)
		
	def __str__(self):
		return '%s { %s }' % (self.name, ' '.join(map(_css,self.children)))
	
__all__.append('Property')
class Property(CSSNode):
	'''Class for specifying a css property in a block
	
	>>> print Property('background', 'transparent')
	background: transparent;
	>>> print Property('padding', 0, Units.Px(0), Units.In(15), Units.Px(15))
	padding: 0 0 15in 15px;
	
	A single keyword provided as a lower-cased unit name is appended to the list
	of values, transformed into a unitted value. Output with more than one
	keyword input is undefined and not recommended. 
	
	>>> print Property('width', px=100)
	width: 100px;
	>>> print Property('border-left', 'solid', 'black', em=1)
	border-left: solid black 1em;
	
	If value is an iterable, all members are transformed and appended to the
	list of children.
	
	>>> print Property('padding', px=[0,0,25,50])
	padding: 0 0 25px 50px;
	
	The special keyword 'important' appends '!important' to the list of children
	if it's set to a true value.
	>>> print Property('position', 'absolute', important=True)
	position: absolute !important;
	'''
	def __init__(self, name, *values, **units):
		important = units.pop('important', False)
		values = list(values)
		if units:
			unit = units.keys()[0].title()
			if unit[0] == '_':
				unit = unit[1:]
			values.extend(map(Units[unit], sequence(units.values()[0])))
		if important:
			values.append('!important')
		super(Property, self).__init__(name, *values)

	def __str__(self):
		return '%s: %s;' % (self.name, ' '.join(map(_css,self.children)))

Attributes = container(
	background = partial(Property, 'background')
)

__all__.append('Selector')
class Selector(CSSNode):
	'''Class for specifying a css element selector
	
	Match elements by type
	
	>>> print Selector('input')
	input
	
	Match elements by class
	
	>>> print Selector(_class='important')
	.important
	
	Match elements by id
	
	>>> print Selector('div', _id='content')
	div#content
	
	Match elements by ancestry
	>>> print Selector('div', Selector('p'))
	div p
	>>> print Selector('div', _child=Selector('p'))
	div>p
	
	Match elements with a certain state
	>>> print Selector('a', _state='hover')
	a:hover
	
	'''
	def __str__(self):
		result = ''
		if self.name:
			result += self.name
		_class = self.get('_class')
		if _class: result += '.'+_class
		_id = self.get('_id')
		if _id: result += '#'+_id
		_state = self.get('_state')
		if _state: result += ':'+_state
		_child = self.get('_child')
		if _child: result += '>'+str(_child)
		return ' '.join([result] + map(str,self.children))

Units = container(
	Px = lambda i:'%gpx'%i if i else '0',
	In = lambda i:'%gin'%i if i else '0',
	Cm = lambda i:'%gcm'%i if i else '0',
	Mm = lambda i:'%gmm'%i if i else '0',
	Em = lambda i:'%gem'%i if i else '0',
	Ex = lambda i:'%gex'%i if i else '0',
	Pt = lambda i:'%gpt'%i if i else '0',
	Pc = lambda i:'%gpc'%i if i else '0',
	Pct = lambda i:'%g%%'%i if i else '0',
	S = lambda i:'%gs'%i,
)

### Factory functions for properties that accept units as arguments
for name in """animation animation-name animation-duration animation-timing-function
animation-delay animation-iteration-count animation-direction animation-play-state
background background-attachment background-color background-image background-position
background-repeat background-clip background-origin background-size
border border-bottom border-bottom-color border-bottom-style border-bottom-width
border-color border-left border-left-color border-left-style border-left-width
border-right border-right-color border-right-style border-right-width border-style
border-top border-top-color border-top-style border-top-width border-width
border-radius border-bottom-left-radius border-bottom-right-radius
border-top-left-radius border-top-right-radius
border-image border-image-outset border-image-repeat border-image-slice border-image-source border-image-width
outline outline-color outline-style outline-width
box-decoration-break box-shadow
overflow-x overflow-y overflow-style rotation rotation-point
color-profile opacity rendering-intent
bookmark-label bookmark-level bookmark-target float-offset
hyphenate-after hyphenate-before hyphenate-character hyphenate-lines hyphenate-resource
hyphens image-resolution marks string-set
width height max-height min-height max-width min-width
box-align box-direction box-flex box-flex-group box-lines box-ordinal-group box-orient box-pack
font font-family font-size font-style font-variant font-weight font-size-adjust font-stretch
content counter-increment counter-reset quotes crop move-to page-policy
grid-columns grid-rows target target-name target-new target-position
alignment-adjust alignment-baseline baseline-shift dominant-baseline
drop-initial-after-adjust drop-initial-after-align drop-initial-before-adjust drop initial-before-align
drop-initial-size drop-initial-value inline-box-align text-height
line-stacking line-stacking-ruby line-stacking-shift line-stacking-strategy
list-style list-style-image list-style-position list-style-type
margin margin-left margin-right margin-top margin-bottom
marquee-direction marquee-play-count marquee-speed marquee-style
column-count column-fill column-gap column-rule column-rule-color column-rule-style
column-rule-width column-span column-width columns
padding padding-left padding-right padding-top padding-bottom
fit fit-position image-orientation page size
bottom clear clip cursor display float left overflow position right top visibility z-index
orphans page-break-after page-break-before page-break-inside widows
ruby-align ruby-overhang ruby-position ruby-span
mark mark-after mark-before phonemes rest rest-after rest-before
voice-balance voice-duration voice-pitch voice-pitch-range voice-rate voice-stress voice-volume
border-collapse border-spacing caption-side empty-cells table-layout
color direction letter-spacing line-height text-align text-decoration text-indent text-transform
unicode-bidi vertical-align white-space word-spacing hanging-punctuation punctuation-trim
text-align-last text-justify text-outline text-overflow text-shadow text-wrap
word-break word-wrap
transform transform-origin transform-style perspective perspective-origin backface-visibility
transition transition-property transition-duration transition-timing-function transition-delay
appearance box-sizing icon nav-down nav-index nav-left nav-right nav-up outline-offset resize
""".split():
	globals()[name.upper().replace('-','_')] = partial(Property,name.lower().replace('_','-'))
	assert str(globals()[name.upper().replace('-','_')](0)) == '%s: 0;'%name.lower().replace('_','-'), str(globals()[name.upper()]())

def css(**attributes):
	return [globals()[name.upper().replace('-','_')](*sequence(value)) for name,value in attributes.items()]

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

if __name__=='__main__':
	import doctest
	doctest.testmod()
