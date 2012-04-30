"""Construct css style sheets from abstract structure

>>> print CSSBlock(CSSSelector('div'),
...     CSSAttribute('padding', '0', Units.Px(20), Units.Px(15)),
...     CSSAttribute('background', 'transparent'),
...     CSSAttribute('border', Units.Px(1), 'solid', Colors.Black),
... )
div { padding: 0 20px 15px; background: transparent; border: 1px solid #000000; }

As a shortcut, selectors can be given as strings, and attributes as dictionaries

>>> a = CSSBlock('a', {'color': Colors.Red})
>>> print a
a { color: #FF0000; }

Nodes are created from these values, so they can be accessed and manipulated
later.

>>> a.name['_state'] = 'hover'
>>> print a
a:hover { color: #FF0000; }
"""

from common import *
from node import *

from functools import partial

def _css(value):
	return str(value)

__all__ = ['CSSNode']
class CSSNode(Node):
	pass

__all__.append('CSSBlock')
class CSSBlock(CSSNode, NoAttributesMixin):
	def __init__(self, name=None, *children, **attributes):
		if not isinstance(name, CSSNode): name = CSSSelector(name)
		mychildren = []
		for child in children:
			if isinstance(child, dict):
				mychildren.extend(CSSAttribute(prop,*sequence(val)) for prop,val in child.items())
			else:
				mychildren.append(child)
		super(CSSBlock, self).__init__(name, *mychildren, **attributes)
		
	def __str__(self):
		return '%s { %s }' % (self.name, ' '.join(map(_css,self.children)))
	
__all__.append('CSSAttribute')
class CSSAttribute(CSSNode):
	'''Class for specifying a css property in a block
	
	>>> print CSSAttribute('background', 'transparent')
	background: transparent;
	>>> print CSSAttribute('padding', 0, Units.Px(0), Units.In(15), Units.Px(15))
	padding: 0 0 15in 15px;
	'''
	def __str__(self):
		return '%s: %s;' % (self.name, ' '.join(map(_css,self.children)))

Attributes = container(
	background = partial(CSSAttribute, 'background')
)

__all__.append('CSSSelector')
class CSSSelector(CSSNode):
	'''Class for specifying a css element selector
	
	Match elements by type
	
	>>> print CSSSelector('input')
	input
	
	Match elements by class
	
	>>> print CSSSelector(_class='important')
	.important
	
	Match elements by id
	
	>>> print CSSSelector('div', _id='content')
	div#content
	
	Match elements by ancestry
	>>> print CSSSelector('div', CSSSelector('p'))
	div p
	>>> print CSSSelector('div', _child=CSSSelector('p'))
	div>p
	
	Match elements with a certain state
	>>> print CSSSelector('a', _state='hover')
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

def Width(value=None, **units):
	if units:
		value = Units[units.keys()[0].title()](units.values()[0])
	return CSSAttribute('width', value)

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
)

rgb = lambda r,g,b:'#%02X%02X%02X'%(r,g,b)
Colors = container(
	from_rgb = rgb,
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
