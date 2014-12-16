# -*- coding: utf-8 -*-

class Value(object):
    """docstring for Value"""
    def __init__(self, domain, value):
        super(Value, self).__init__()
        self._domain = domain
        if not domain.contains(value):
            raise DomainError("value {} not in domain".format(value))
        self._value = value

    @property
    def value(self):
        return self._value

    def __str__(self):
        return 'Value({})'.format(self.value)
    
    def __add__(self, term):
        return self._domain.step(self._value, term)

    def __radd__(self, term):
        return self.__add__(self._value, term)

    def __sub__(self, term):
        return self._domain.step(self._value, -term)

    def __rsub__(self, term):
        return self.__sub__(self._value, term)


class DomainError(Exception): pass


class Domain(object):
    """docstring for Domain"""

    def __getitem__(self, value):
        if not self.contains(value):
            raise DomainError('value {} is not in this domain'.format(value))
        return Value(self, value)

    def contains(self, value):
        # Should return a boolean indicating whether value is in domain
        raise NotImplementedError()

    def step(self, value, step):
        # Should return a new Value object in this Domain
        raise NotImplementedError()

class Interval(Domain):
    """docstring for Interval"""
    def __init__(self, start, stop, cycle=False, type=None):
        super(Interval, self).__init__()
        self._start = start
        self._stop = stop
        self._length = stop - start
        self._cycle = cycle
        self._type = type

    def contains(self, value):
        if self._type:
            if not isinstance(value, type):
                return False

        return self._start <= value <= self._stop

    def step(self, value, step):
        assert self.contains(value)

        if self._cycle:
            result = (value + step - self._start) % self._length + self._start
        else:
            result = value + step
        
        return self[result]


class OrderedSet(Domain):
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
            raise DomainError('cannot step outside domain')
        return self[value]
