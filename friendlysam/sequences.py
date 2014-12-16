# -*- coding: utf-8 -*-

class Item(object):
    """docstring for Item"""
    def __init__(self, sequence, value):
        super(Item, self).__init__()
        self._sequence = sequence
        if not sequence.contains(value):
            raise SequenceError("value {} not in sequence".format(value))
        self._value = value

    @property
    def value(self):
        return self._value

    def __str__(self):
        return 'Item({})'.format(self.value)
    
    def __add__(self, term):
        return self._sequence.step(self._value, term)

    def __radd__(self, term):
        return self.__add__(self._value, term)

    def __sub__(self, term):
        return self._sequence.step(self._value, -term)

    def __rsub__(self, term):
        return self.__sub__(self._value, term)

    def __cmp__(self, other):
        return cmp(self.value, other)


class SequenceError(Exception): pass


class Sequence(object):
    """docstring for Sequence"""

    def __getitem__(self, value):
        if not self.contains(value):
            raise SequenceError('value {} is not in this sequence'.format(value))
        return Item(self, value)

    def contains(self, value):
        # Should return a boolean indicating whether value is in sequence
        raise NotImplementedError()

    def step(self, value, step):
        # Should return a new Item object in this Sequence
        raise NotImplementedError()

class Integers(Sequence):
    """docstring for Integers"""
    def __init__(self, start, stop, cycle=False):
        super(Integers, self).__init__()
        self._start = start
        self._stop = stop
        self._length = stop - start
        self._cycle = cycle
        self._type = type

    def contains(self, value):
        return isinstance(value, int) and self._start <= value <= self._stop

    def step(self, value, step):
        assert self.contains(value)

        if self._cycle:
            result = (value + step - self._start) % self._length + self._start
        else:
            result = value + step
        
        return self[result]


class OrderedSet(Sequence):
    """docstring for OrderedSet"""
    def __init__(self, values, cycle=False):
        super(OrderedSet, self).__init__()
        self._values = tuple(v for v in values)
        self._indices = {val: index for index, val in enumerate(self._values)}
        self._cycle = cycle

    def contains(self, value):
        return value in self._values

    def step(self, value, step):
        index = self._indices[value] + step
        if self._cycle:
            index = index % len(self._values)
        try:
            value = self._values[index]
        except IndexError:
            raise SequenceError('cannot step outside sequence')
        return self[value]