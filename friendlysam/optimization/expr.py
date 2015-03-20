# -*- coding: utf-8 -*-

class Expression(object):
    """docstring for Expression"""
    
    def __add__(self, other):
        return Add(self, other)

    def __radd__(self, other):
        return Add(other, self)

    def __sub__(self, other):
        return Sub(self, other)

    def __rsub__(self, other):
        return Sub(other, self)

    def __mul__(self, other):
        return Mul(self, other)

    def __rmul__(self, other):
        return Mul(other, self)

    def __pow__(self, other):
        return Pow(self, other)

    def __neg__(self):
        return -1 * self


class _BinaryOp(Expression):
    """docstring for _BinaryOp"""
    def __init__(self, a, b):
        super(_BinaryOp, self).__init__()
        self._a = a
        self._b = b

    @property
    def a(self):
        return self._a
    
    @property
    def b(self):
        return self._b


class Add(_BinaryOp):
    """docstring for Add"""

    def __new__(cls, a, b):
        if a == 0:
            return b
        if b == 0:
            return a
        return super(Add, cls).__new__(cls, a, b)


    def __str__(self):
        return '({} + {})'.format(self.a, self.b)


class Sub(_BinaryOp):
    """docstring for Sub"""
    
    def __new__(cls, a, b):
        if a == 0:
            return -b
        if b == 0:
            return a
        return super(Sub, cls).__new__(cls, a, b)


    def __str__(self):
        return '({} - {})'.format(self.a, self.b)
        
    
class Mul(_BinaryOp):
    """docstring for Mul"""
    
    def __new__(cls, a, b):
        if a == 0 or b == 0:
            return 0
        elif b == 1:
            return a
        elif a == 1:
            return b

        return super(Mul, cls).__new__(cls, a, b)


    def __str__(self):
        return '({} * {})'.format(self.a, self.b)

class Variable(Expression):
    """docstring for Variable"""
    def __init__(self, name=None):
        super(Variable, self).__init__()
        self._name = '<unnamed>' if name is None else name

    def __str__(self):
        return self._name
