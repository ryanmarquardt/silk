
from .. import flatten, is_sequence
from collections import MutableMapping, MutableSequence


def is_string(x):
    return isinstance(x, str)


class Entity(MutableMapping):
    '''
    Represents an indivisible token in a document.

    >>> Entity('html', _lang='en')
    Entity('html', _lang='en')

    >>> class HTMLStartEntity(Entity):
    ...     def __str__(self):
    ...         return '<%s%s>' % (self.name, ''.join(
    ...             ' %s=%r' % i for i in self.attributes.items()))

    >>> h = HTMLStartEntity('html', lang='en'); print(h)
    <html lang='en'>

    >>> h._lang = 'ru'; print(h)
    <html lang='ru'>

    >>> del h['lang']; print(h)
    <html>
    '''
    def __init__(self, name, **attributes):
        vars(self)['name'] = name
        vars(self)['attributes'] = {}
        for k, v in attributes.items():
            if k[0] == '_':
                k = k[1:]
            self.attributes[k] = v

    def __getitem__(self, key):
        return self.attributes[key]

    def __getattr__(self, key):
        if key[0] == '_':
            key = key[1:]
        return self.get(key)

    def __setitem__(self, key, value):
        self.attributes[key] = value

    def __setattr__(self, key, value):
        if key[0] == '_':
            key = key[1:]
        self.__setitem__(key, value)

    def __delitem__(self, key):
        del self.attributes[key]

    def __delattr__(self, key):
        if key[0] == '_':
            key = key[1:]
        self.__delitem__(key)

    def __iter__(self):
        return iter(self.attributes)

    def __len__(self):
        return len(self.attributes)

    def __bool__(self):
        return True

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join(
                [repr(self.name)] +
                ['_%s=%r' % i for i in self.attributes.items()]),
        )


class Node(MutableMapping, MutableSequence):
    '''
    A list of entities, used for organizing them into a tree

    >>> Node.new('x')
    <class 'abc.Node'>
    >>> Node.new('x')()
    Node('x')()
    >>> Node.new('y')(1, 2, 3, a=5)
    Node('y')(1, 2, 3, _a=5)
    >>> n = Node.new('n')(r='s')
    >>> n.append('o')
    >>> n.extend(['p', 'z'])
    >>> n[-1] = 'q'
    >>> n['r'] = 'r'
    >>> n
    Node('n')('o', 'p', 'q', _r='r')
    >>> n.update(_s='t', r=0)
    >>> del n['r']
    >>> n.pop(1)
    'p'
    >>> n
    Node('n')('o', 'q', _s='t')

    An underscore '_' is prepended to all attribute names to allow for
    attribute names that are also python keywords such as 'class', which is a
    valid concern e.g. in xml. To set set a literal attribute '_name', use two
    underscores: '__name'. repr() is unaffected so that eval(repr(Node(...)))
    evaluates to the original Node value.

    >>> a = Node.new('a')(_class='123')
    >>> a
    Node('a')(_class='123')
    >>> a['class'] = '234'
    >>> a
    Node('a')(_class='234')
    >>> print(a)
    a(class='234')

    Set and retrieve attributes on the object that start with an underscore. If
    that attribute doesn't exist, None is returned (similar to dict.get()).

    >>> a._class = '345'
    >>> print(a)
    a(class='345')
    >>> print(a._class)
    345
    >>> print(a._milk)
    None

    Normal attribute access isn't so lucky

    >>> a.milk
    Traceback (most recent call last):
     ...
    AttributeError: 'Node' object has no attribute 'milk'

    If the first argument is another node, that node's values are copied. The
    other arguments are ignored.

    >>> b = a.copy()
    >>> b
    Node('a')(_class='345')
    >>> b.children is a.children
    False
    >>> b.attributes is a.attributes
    False
    >>> is_sequence(Node())
    False

    Use Node.walk to iterate over its entire tree.

    >>> doc = Node.new('a')(Node.new('b')('c', Node.new('d')(e='f')))
    >>> for depth, element in doc.walk():
    ...   if isinstance(element, Node):
    ...     print('  '*depth, element.name, element.attributes)
    ...   else:
    ...     print('  '*depth, repr(element))
     a {}
       b {}
         'c'
         d {'_e': 'f'}
    '''
    name = None
    __sequence__ = False

    def __init__(self, *children, **attributes):
        self.children = flatten(children)
        self.attributes = {self._attr_key(k): v for k, v in
                           attributes.items()}

    @classmethod
    def new(cls, name, classname=None):
        return type(classname or cls.__name__, (cls,), {'name': name})

    def copy(self):
        return self.__class__(*self.children, **self.attributes)

    @staticmethod
    def _attr_key(key):
        return key if key[0] == '_' else '_' + key

    def __getitem__(self, key):
        if is_string(key):
            return self.__dict__['attributes'][self._attr_key(key)]
        else:
            return self.__dict__['children'][key]

    def __getattr__(self, key):
        if key[0] == '_':
            return self.get(key)
        else:
            return super(Node, self).__getattribute__(key)

    def __setitem__(self, key, value):
        if is_string(key):
            self.__dict__['attributes'][self._attr_key(key)] = value
        else:
            if is_sequence(value):
                del self.__dict__['children'][key]
                for v in reversed(flatten(value)):
                    self.__dict__['children'].insert(key, value)
            else:
                self.__dict__['children'][key] = value

    def __setattr__(self, key, value):
        if key[0] == '_':
            self.__setitem__(key, value)
        else:
            super(Node, self).__setattr__(key, value)

    def __delitem__(self, key):
        if is_string(key):
            del self.attributes[self._attr_key(key)]
        else:
            del self.children[key]

    def __len__(self):
        return len(self.children)

    def insert(self, place, value):
        for v in reversed(flatten(value)):
            self.children.insert(place, v)

    def _real_attrs(self):
        return dict((k[1:], v) if k[0] == '_' else (k, v) for k, v in
                    self.attributes.items())

    def __repr__(self):
        return '%s%s(%s)' % (
            self.__class__.__name__,
            ('('+repr(self.name)+')') if self.name else '',
            ', '.join(
                [repr(x) for x in self.children] +
                ['%s=%r' % i for i in self.attributes.items()]
            )
        )

    def __str__(self):
        return '%s(%s)' % (
            self.name, ', '.join(
                [repr(x) for x in self.children] +
                ['%s=%r' % i for i in self._real_attrs().items()])
        )

    def __bool__(self):
        return True

    def walk(self, filter=None, depth=0):
        filter = filter or (lambda x: True)
        if filter(self):
            yield depth, self
        for element in self.children:
            if hasattr(element, 'walk'):
                for d, sub in element.walk(filter=filter, depth=depth + 1):
                    if filter(sub):
                        yield d, sub
            else:
                if filter(element):
                    yield depth+1, element

__all__ = ['Entity', 'Node']
