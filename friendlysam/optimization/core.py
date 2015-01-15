# -*- coding: utf-8 -*-

from friendlysam.log import get_logger
logger = get_logger(__name__)

import itertools

from enum import Enum

class Domain(Enum):
    """docstring for Domain"""
    real = 0
    integer = 1
    binary = 2

DEFAULT_DOMAIN = Domain.real


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

class Variable(object):
    """docstring for Variable"""

    def __init__(self, name=None, lb=None, ub=None, domain=DEFAULT_DOMAIN):
        super(Variable, self).__init__()
        self.owner = None
        self._name = name
        self._lb = lb
        self._ub = ub
        self._domain = domain
        self._values = {}

    @property
    def engine(self):
        return self.owner.engine

    def name(self, index):
        if index is None:
            return self._name
        else:
            return '{}[{}]'.format(self._name, index)

    @property
    def domain(self):
        return self._domain
        
    @property
    def lb(self):
        return self._lb

    @property
    def ub(self):
        return self._ub

    def _value_or_symbol(self, *index):
        if index in self._values:
            return self._values[index]
        else:
            return self.engine.get_variable(self, index)
        
    def __call__(self, *index):
        return self._value_or_symbol(*index)

    def take_value(self, solution, *index):
        self[index] = solution[self, index]

    def __setitem__(self, index, value):
        self.engine.delete_variable(self, index)
        self._values[index] = value

    def constraint_func(self, index):
        # Not used in this implementation, but in principle a Variable may produce constraints
        # which should be added to to any optimization problem where the variable is used.
        # This was used to produce upper and lower bounds in the previous implementation 
        # which used sympy symbols instead of Pyomo variables.
        #
        # It is still used in the subclass PiecewiseAffineArg.
        return set()



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
    def __init__(self, engine=None, constraints=None, objective=None):
        super(Problem, self).__init__()
        self.constraints = set() if constraints is None else constraints
        self.objective = objective
        self.engine = engine

    @property
    def engine(self):
        return self._engine
    @engine.setter
    def engine(self, value):
        self._engine = value

    def solve(self):
        """Try to solve the optimization problem"""
        raise NotImplementedError()