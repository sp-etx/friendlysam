# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import super
from builtins import str
from future import standard_library
standard_library.install_aliases()
from friendlysam.log import get_logger
logger = get_logger(__name__)

import itertools
from enum import Enum

from friendlysam.compat import ignored

class SolverError(Exception): pass
        

class Domain(Enum):
    """docstring for Domain"""
    real = 0
    integer = 1
    binary = 2

DEFAULT_DOMAIN = Domain.real

def _evaluate_or_not(obj, replacements):
    return obj.evaluate(replacements) if hasattr(obj, 'evaluate') else obj

class _Expression(object):
    """docstring for _Expression"""
    def __init__(self, *args):
        super().__init__()
        self._args = tuple(args)

    def evaluate(self, replacements):
        return self._evaluate(*(_evaluate_or_not(a, replacements) for a in self._args))

    @property
    def value(self):
        return float(self.evaluate({}))

    @property
    def leaves(self):
        leaves = set()
        for a in self._args:
            try:
                leaves.update(a.leaves)
            except AttributeError:
                leaves.add(a)
        return leaves

    def __str__(self):
        return self._format.format(*self._args)

class Relation(_Expression):

    @property
    def expr(self):
        return self


class LessEqual(Relation):
    _format = '({} <= {})'

    def _evaluate(self, a, b):
        return a <= b

class GreaterEqual(Relation):
    _format = '({} >= {})'

    def _evaluate(self, a, b):
        return a >= b

class Equals(Relation):
    _format = '({} == {})'

    def _evaluate(self, a, b):
        return a == b

class _MathEnabled(object):
    """docstring for _MathEnabled"""

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

    def __hash__(self):
        return id(self)


class Add(_Expression, _MathEnabled):
    """docstring for Add"""
    _format = '({} + {})'

    def _evaluate(self, a, b):
        return a + b


class Sub(_Expression, _MathEnabled):
    """docstring for Sub"""
    _format = '({} - {})'

    def _evaluate(self, a, b):
        return a - b
        
    
class Mul(_Expression, _MathEnabled):
    """docstring for Mul"""
    
    _format = '({} * {})'

    def _evaluate(self, a, b):
        return a * b


class Variable(_MathEnabled):
    """docstring for Variable"""

    def __init__(self, name=None, lb=None, ub=None, domain=DEFAULT_DOMAIN):
        super().__init__()
        self._name = '<unnamed>' if name is None else name
        self.lb = lb
        self.ub = ub
        self.domain = domain

    def __str__(self):
        return self._name

    @property
    def name(self):
        return self._name


    @property
    def leaves(self):
        return (self,)


    def evaluate(self, replacements=None):
        with ignored(AttributeError):
            return self.value
        with ignored(AttributeError):
            return replacements.get(self, self)
        return self


    def take_value(self, solution):
        self.value = solution[self]


class VariableCollection(object):
    """docstring for VariableCollection"""
    def __init__(self, name=None, **kwargs):
        super().__init__()
        self.name = name
        self._kwargs = kwargs
        self._vars = {}

    def __call__(self, *indices):
        if not indices in self._vars:
            name = '{}{}'.format(self.name, indices)
            self._vars[indices] = Variable(name=name, **self._kwargs)
        return self._vars[indices]


class ConstraintError(Exception): pass


class _ConstraintBase(object):
    """docstring for _ConstraintBase"""
    def __init__(self, desc=None, origin=None):
        super().__init__()
        self.desc = desc
        self.origin = origin

class Constraint(_ConstraintBase):
    """docstring for Constraint"""
    def __init__(self, expr, desc=None, **kwargs):
        super().__init__(desc=desc, **kwargs)
        self.expr = expr

    def __str__(self):
        return str(self.expr)


class _SOS(_ConstraintBase):
    """docstring for _SOS"""
    def __init__(self, sostype, symbols, **kwargs):
        super().__init__(**kwargs)
        if not (isinstance(symbols, tuple) or isinstance(symbols, list)):
            raise ConstraintError('symbols must be a tuple or list')
        self._symbols = tuple(symbols)
        self._sostype = sostype

    def __str__(self):
        return 'SOS{}{}'.format(self._sostype, self._symbols)

    @property
    def symbols(self):
        return self._symbols


class SOS1(_SOS):
    """docstring for SOS1"""
    def __init__(self, symbols, **kwargs):
        super().__init__(1, symbols, **kwargs)


class SOS2(_SOS):
    """docstring for SOS2"""
    def __init__(self, symbols, **kwargs):
        super().__init__(2, symbols, **kwargs)


class _Objective(object):
    """docstring for _Objective"""
    def __init__(self, expr):
        super().__init__()
        self.expr = expr

class Maximize(_Objective):
    """docstring for Maximize"""
    pass

class Minimize(_Objective):
    """docstring for Minimize"""
    pass


class PiecewiseAffine(object):
    """docstring for PiecewiseAffine"""
    def __init__(self, points, name=None):
        self._name_base = name
        self._points = tuple(p for p in points)
        self._weights = tuple(self._make_variable(p) for p in points)
        self._arg = self.func(self._points)

        self._constraints = (
            SOS2(self._weights, desc='PiecewiseAffine weights'),
            Constraint(sum(self._weights) == 1, desc='PiecewiseAffine sum of weights'))


    @property
    def weights(self):
        return self._weights


    @property
    def points(self):
        return self._points


    @property
    def constraints(self):
        return self._constraints


    @property
    def arg(self):
        return self._arg


    def _make_variable(self, point):
        return Variable(
            name='{}_{}'.format(self._name_base, point),
            lb=0,
            ub=1,
            domain=Domain.real)

    def func(self, values):
        return sum(val * weight for val, weight in zip(values, self._weights))


class Problem(object):
    """An optimization problem"""
    def __init__(self, constraints=None, objective=None):
        super().__init__()
        self._constraints = set() if constraints is None else constraints
        self.objective = objective

    @property
    def constraints(self):
        return self._constraints

    def add_constraints(self, constraints):
        self._constraints.update(constraints)

    def solve(self):
        """Try to solve the optimization problem"""
        raise NotImplementedError()
