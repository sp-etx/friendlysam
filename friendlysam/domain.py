# -*- coding: utf-8 -*-

import sympy

class DomainError(Exception): pass
    
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

        

class Domain(object):
    """docstring for Domain"""
    def __init__(self, length=0, start=0, cycle=False):
        super(Domain, self).__init__()

        self.cycle = cycle
        self._start = start
        self._length = length

    def __getitem__(self, value):
        return Value(self, value)

    def _get_index(self, value):
        index = value - self._start
        if not self._contains_index(index):
            raise DomainError("value {} not in domain".format(value))
        return index

    def _get_value(self, index):
        return index + self._start

    def _contains_index(self, index):
        return 0 <= index < self._length
    
    def contains(self, value):
        index = self._get_index(value)
        return self._contains_index(index)

    def step(self, value, step):
        index = self._get_index(value) + step
        if self.cycle:
            index = index % self._length
        value = self._get_value(index)
        return self[value]



class MapDomain(object):
    """docstring for MapDomain"""
    def __init__(self, values, cycle=False):
        super(MapDomain, self).__init__()
        self._values = tuple(v for v in values)
        self._indices = {val: index for index, val in enumerate(values)}
        self.cycle = cycle

    def __getitem__(self, value):
        return Value(self, value)

    def contains(self, value):
        return value in self._values

    def step(self, value, step):
        index = self._indices[value] + step
        if self.cycle:
            index = index % len(self._values)
        value = self._values[index]
        return self[value]

class Process(object):
    """docstring for Process"""
    def __init__(self):
        super(Process, self).__init__()
        self._inflow = {}

    def __str__(self):
        return 'Process'

    def inflow(self, time):
        if not time in self._inflow:
            self._inflow[time] = sympy.Symbol(str(self) + '.inflow(' + str(time) + ')')

        return self._inflow[time]

    def constraints(self, time):
        return self.inflow(time) - self.inflow(time - 1) < 5

dom = MapDomain(range(50), cycle=True)

p = Process()
print(p.constraints(dom[5]))

