# -*- coding: utf-8 -*-

class Indexed(object):
    """A collection where missing elements are created on demand.

    An Indexed object is dict-like: you can access items in it based on
    index just like a dictionary. The difference is that requests for 
    items that do not exist are replaced by a function call.
    trying to access 

    An Indexed object is similar to a `defaultdict`, except that the
    constructor signature is different, and that the index is passed
    to the function for generating missing items.

    Args:
        func (callable): A callable used to create missing items. The
            callable should take exactly one argument.

    Example:
        >>> from util import Indexed
        >>> d = Indexed(lambda idx: idx * 10)
        >>> d[5]
        50
        >>> d[5]='my string'
        >>> d[5]
        'my string'
        >>> d[2] = 'another string'
        >>> d[2]
        'another string'
    """
    def __init__(self, func):
        super(Indexed, self).__init__()
        self._func = func
        self._items = {}


    def __getitem__(self, index):
        if not index in self._items:
            self._items[index] = self._func(index)
        return self._items[index]

    def __setitem__(self, index, value):
        self._items[index] = value