# -*- coding: utf-8 -*-
from friendlysam.compat import ignored
import numbers


class Expression(object):
    """docstring for Expression"""

    @property
    def symbols(self):
        raise NotImplementedError()    
    
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

    def __neg__(self):
        return -1 * self

    def __le__(self, other):
        return LessEqual(self, other)

    def __ge__(self, other):
        return GreaterEqual(self, other)

    def __lt__(self, other): raise NotImplementedError()

    def __gt__(self, other): raise NotImplementedError()

    def replace(self, replacements):
        raise NotImplementedError()


class _Numeric(Expression):
    """docstring for _Numeric"""
    def replace(self, replacements):
        return self

class Float(float, _Numeric): pass    

class Int(int, _Numeric): pass

def _ensure_expr(expr):
    if isinstance(expr, float): return Float(expr)
    if isinstance(expr, int): return Int(expr)
    assert isinstance(expr, Expression)
    return expr


class _BinaryOp(Expression):
    """docstring for _BinaryOp"""
    def __init__(self, a, b):
        super(_BinaryOp, self).__init__()
        self._a = _ensure_expr(a)
        self._b = _ensure_expr(b)

    @property
    def symbols(self):
        symbols = set()
        with ignored(AttributeError):
            symbols.update(self._a.symbols)
            symbols.update(self._b.symbols)
        assert all(isinstance(s, Symbol) for s in symbols)
        return symbols

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


    def replace(self, replacements):
        return self._a.replace(replacements) + self._b.replace(replacements)


class LessEqual(_BinaryOp):
    """docstring for LessEqual"""

    def __new__(cls, a, b):
        return super(LessEqual, cls).__new__(cls, a, b)


    def __str__(self):
        return '({} <= {})'.format(self.a, self.b)


    def replace(self, replacements):
        return self._a.replace(replacements) <= self._b.replace(replacements)


class GreaterEqual(_BinaryOp):
    """docstring for GreaterEqual"""

    def __new__(cls, a, b):
        return super(GreaterEqual, cls).__new__(cls, a, b)


    def __str__(self):
        return '({} >= {})'.format(self.a, self.b)


    def replace(self, replacements):
        return self._a.replace(replacements) >= self._b.replace(replacements)

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

    def replace(self, replacements):
        return self._a.replace(replacements) - self._b.replace(replacements)
        
    
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


    def replace(self, replacements):
        return self._a.replace(replacements) * self._b.replace(replacements)


class Symbol(Expression):
    """docstring for Symbol"""
    def __init__(self, name=None):
        super(Symbol, self).__init__()
        self._name = '<unnamed>' if name is None else name

    @property
    def symbols(self):
        return {self}

    def __str__(self):
        return self._name

    def replace(self, replacements):
        return replacements[self]
