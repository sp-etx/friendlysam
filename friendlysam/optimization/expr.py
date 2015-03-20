# -*- coding: utf-8 -*-
from friendlysam.compat import ignored
import numbers

def _replace_or_not(obj, replacements):
    return obj.replace(replacements) if hasattr(obj, 'replace') else obj

class _BinaryOperation(object):
    """docstring for _BinaryOperation"""
    def __init__(self, a, b):
        super(_BinaryOperation, self).__init__()
        self._args = a, b

    @property
    def symbols(self):
        raise NotImplementedError()

    def replace(self, replacements):
        args = (_replace_or_not(arg, replacements) for arg in self._args)
        return self._evaluate(*args)

    def __str__(self):
        return self._format.format(*self._args)


class LessEqual(_BinaryOperation):
    _nargs = 2
    _format = '({} <= {})'

    def _evaluate(self, a, b):
        return a <= b

class GreaterEqual(_BinaryOperation):
    _nargs = 2
    _format = '({} >= {})'

    def _evaluate(self, a, b):
        return a >= b

class Equals(_BinaryOperation):
    _nargs = 2
    _format = '({} == {})'

    def _evaluate(self, a, b):
        return a == b

class _Expression(object):
    """docstring for _Expression"""

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

    def __eq__(self, other):
        return Equals(self, other)

    def __lt__(self, other): raise NotImplementedError()

    def __gt__(self, other): raise NotImplementedError()


class _BinaryExpr(_Expression, _BinaryOperation): pass        

class Add(_BinaryExpr):
    """docstring for Add"""
    _format = '({} + {})'

    def _evaluate(self, a, b):
        return a + b


class Sub(_BinaryExpr):
    """docstring for Sub"""
    _format = '({} - {})'

    def _evaluate(self, a, b):
        return a - b
        
    
class Mul(_BinaryExpr):
    """docstring for Mul"""
    
    _format = '({} * {})'

    def _evaluate(self, a, b):
        return a * b


class Symbol(_Expression):
    """docstring for Symbol"""
    def __init__(self, name=None):
        super(Symbol, self).__init__()
        self._name = '<unnamed>' if name is None else name

    def __str__(self):
        return self._name

    def replace(self, replacements):
        return replacements.get(self, self)
