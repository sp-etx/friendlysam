# -*- coding: utf-8 -*-

from friendlysam.log import get_logger
logger = get_logger(__name__)

import itertools
from enum import Enum

from friendlysam import NOINDEX
from friendlysam.compat import ignored

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
        super(_Expression, self).__init__()
        self._args = tuple(args)

    def evaluate(self, replacements):
        return self._evaluate(*(_evaluate_or_not(a, replacements) for a in self._args))

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


class LessEqual(_Expression):
    _format = '({} <= {})'

    def _evaluate(self, a, b):
        return a <= b

class GreaterEqual(_Expression):
    _format = '({} >= {})'

    def _evaluate(self, a, b):
        return a >= b

class Equals(_Expression):
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
        super(Variable, self).__init__()
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

    def constraint_func(self, index=NOINDEX):
        # Not used in this implementation, but in principle a Variable may produce constraints
        # which should be added to to any optimization problem where the variable is used.
        # This was used to produce upper and lower bounds in the previous implementation 
        # which used sympy symbols instead of Pyomo variables.
        #
        # It is still used in the subclass PiecewiseAffineArg.
        return set()


class VariableCollection(object):
    """docstring for VariableCollection"""
    def __init__(self, name=None, **kwargs):
        super(VariableCollection, self).__init__()
        self.name = name
        self._kwargs = kwargs
        self._vars = {}

    def __getitem__(self, index):
        if not index in self._vars:
            name = '{}[{}]'.format(self.name, index)
            self._vars[index] = Variable(name=name, **self._kwargs)
        return self._vars[index]


class ConstraintError(Exception): pass


class _ConstraintBase(object):
    """docstring for _ConstraintBase"""
    def __init__(self, desc=None):
        super(_ConstraintBase, self).__init__()
        self.desc = desc

    def _add_desc(self, s):
        if self.desc is None:
            return s
        else:
            return '{} ({})'.format(s, self.desc)
        

class Constraint(_ConstraintBase):
    """docstring for Constraint"""
    def __init__(self, expr, desc=None):
        super(Constraint, self).__init__(desc)
        self.expr = expr

    def __str__(self):
        return self._add_desc(str(self.expr))


class _SOS(_ConstraintBase):
    """docstring for _SOS"""
    def __init__(self, sostype, symbols, desc=None):
        super(_SOS, self).__init__(desc)
        if not (isinstance(symbols, tuple) or isinstance(symbols, list)):
            raise ConstraintError('symbols must be a tuple or list')
        self._symbols = tuple(symbols)
        self._sostype = sostype

    def __str__(self):
        return self._add_desc('SOS{}{}'.format(self._sostype, self._symbols))

    @property
    def symbols(self):
        return self._symbols


class SOS1(_SOS):
    """docstring for SOS1"""
    def __init__(self, symbols, desc=None):
        super(SOS1, self).__init__(1, symbols, desc=desc)


class SOS2(_SOS):
    """docstring for SOS2"""
    def __init__(self, symbols, desc=None):
        super(SOS2, self).__init__(2, symbols, desc=desc)


class _Objective(object):
    """docstring for _Objective"""
    def __init__(self, expr):
        super(_Objective, self).__init__()
        self.expr = expr

class Maximize(_Objective):
    """docstring for Maximize"""
    pass

class Minimize(_Objective):
    """docstring for Minimize"""
    pass




# class PiecewiseAffineArg(Variable):
#     """docstring for Variable"""
#     def __init__(self, name, points):
#         super(PiecewiseAffineArg, self).__init__(name)
#         self.points = points
#         SymbolCatalog().register(self, self._symbol_options)

#     def __call__(self, index=None):
#         return self.weighted_sum(index)

#     def weighted_sum(self, index):
#         return sum([point * weight for point, weight in zip(self.points, self.weights(index))])

#     def weights(self, index):
#         cat = SymbolCatalog()
#         return tuple(cat.get(self, (index, point)) for point in self.points)

#     def _symbol_options(self, (index, point)):
#         if index is None:
#             name = '{}_{}'.format(self.name, point)
#         else:
#             name = '{}_{}[{}]'.format(self.name, point, index)

#         return dict(name=name, bounds=(0, 1), domain=Domain.real)
    
#     def replace_symbols(self, data, indices):
#         for index, symbol in indices:
#             for point in self.points:
#                 if symbol in data:
#                     SymbolCatalog().set(self, (index, point), data[symbol])

#     def constraint_func(self, index):
#         weights = self.weights(index)
#         constraints = (
#             SOS2(weights, desc='Weights of points in piecewise affine expression'),
#             Constraint(sum(weights) == 1, desc='Sum of weights in piecewise affine expression'))
#         return constraints


class Problem(object):
    """An optimization problem"""
    def __init__(self, constraints=None, objective=None):
        super(Problem, self).__init__()
        self.constraints = set() if constraints is None else constraints
        self.objective = objective

    def solve(self):
        """Try to solve the optimization problem"""
        raise NotImplementedError()
