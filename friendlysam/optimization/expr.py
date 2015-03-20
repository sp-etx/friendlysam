# -*- coding: utf-8 -*-

#from friendlysam.log import get_logger
#logger = get_logger(__name__)

class _ExprBase(object):
    """docstring for _ExprBase"""
    
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


class _BinaryOp(_ExprBase):
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
    
    def __str__(self):
        return '({} - {})'.format(self.a, self.b)
        
    
class Mul(_BinaryOp):
    """docstring for Mul"""
    
    def __str__(self):
        return '({} * {})'.format(self.a, self.b)


class Pow(_BinaryOp):
    """docstring for Pow"""
    
    def __str__(self):
        return '({}^{})'.format(self.a, self.b)


class Variable(_ExprBase):
    """docstring for Variable"""
    def __init__(self, symbol):
        super(Variable, self).__init__()
        self._symbol = symbol

    def __str__(self):
        return self._symbol


x = Variable('abc')

print(x ** (3 - 2))
print(2 + x ** 3)
print(x * 0)