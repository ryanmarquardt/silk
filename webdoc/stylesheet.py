
class StyleSheet(object):
	def __init__(self):
		self.nodes = []

	def add(self, name, **props):
		if hasattr(name, '__iter__'):
			name = ', '.join(name)
		self.nodes.append((name, props))

	def render(self):
		return '\n'.join(
			'%s { %s }' % (
				name,
				''.join('%s:%s;'%i for i in props.items())
			)
			for name,props in self.nodes
		)
