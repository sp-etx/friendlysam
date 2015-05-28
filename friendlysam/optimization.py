# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)
import sys

from contextlib import contextmanager
from itertools import chain
from enum import Enum
import numbers

from friendlysam.compat import ignored

_namespace_string = ''

def rename_namespace(s):
    global _namespace_string
    if _namespace_string == '':
        return str(s)
    return '{}.{}'.format(_namespace_string, s)

@contextmanager
def namespace(name):
    global _namespace_string
    old = _namespace_string
    _namespace_string = str(name)
    yield
    _namespace_string = old


def get_solver(**kwargs):
    engine = kwargs.pop('engine', 'pulp')

    if engine == 'pulp':            
        from friendlysam.solvers.pulpengine import PulpSolver
        return PulpSolver(**kwargs)

class SolverError(Exception): pass
        

class Domain(Enum):
    """docstring for Domain"""
    real = 0
    integer = 1
    binary = 2

DEFAULT_DOMAIN = Domain.real

def _evaluate_or_not(obj, replacements):
    return obj.evaluate(replacements) if hasattr(obj, 'evaluate') else obj

class _Operation(object):
    """docstring for _Operation"""
    def __init__(self, *args):
        super().__init__()
        for a in args:
            if isinstance(a, VariableCollection):
                msg = (
                    'Cannot apply {} on the VariableCollection {}. '
                    'Did you forget an index?').format(self.__class__, a)
                raise ValueError(msg).with_traceback(sys.exc_info()[2])
        self._args = tuple(args)


    def evaluate(self, replacements):
        return self._evaluate(*(_evaluate_or_not(a, replacements) for a in self._args))

    @property
    def value(self):
        return float(self.evaluate({}))

    @property
    def variables(self):
        return set(l for l in self.leaves if isinstance(l, Variable))

    @property
    def leaves(self):
        leaves = set()
        for a in self._args:
            try:
                leaves.update(a.leaves)
            except AttributeError:
                leaves.add(a)
        return leaves

    def _format_arg(self, arg):
        if isinstance(arg, (numbers.Number, Variable)):
            return str(arg)

        if isinstance(arg, _Operation) and arg._priority >= self._priority:
            return str(arg)
        
        return '({})'.format(arg)

    def __str__(self):
        return self._format.format(*(self._format_arg(a) for a in self._args))

    def __repr__(self):
        return '<{} at {}: {}>'.format(self.__class__.__name__, hex(id(self)), self)

class Relation(_Operation):

    _priority = 0

    def __bool__(self):
        raise RuntimeError("{} is a Relation and its truthyness should not be tested".format(self))


    @property
    def expr(self):
        return self

class LessEqual(Relation):
    _format = '{} <= {}'

    def _evaluate(self, a, b):
        return a <= b

class GreaterEqual(Relation):
    _format = '{} >= {}'

    def _evaluate(self, a, b):
        return a >= b

class Equals(Relation):
    _format = '{} == {}'

    def _evaluate(self, a, b):
        return a == b

def _is_zero(something):
    return isinstance(something, numbers.Number) and something == 0


class _MathEnabled(object):
    """docstring for _MathEnabled"""

    def __add__(self, other):
        return self if _is_zero(other) else Add(self, other)

    def __radd__(self, other):
        return self if _is_zero(other) else Add(other, self)

    def __sub__(self, other):
        return self if _is_zero(other) else Sub(self, other)

    def __rsub__(self, other):
        return -self if _is_zero(other) else Sub(other, self)

    def __mul__(self, other):
        return 0 if _is_zero(other) else Mul(self, other)

    def __rmul__(self, other):
        return 0 if _is_zero(other) else Mul(other, self)

    def __truediv__(self, other):
        return self * (1/other) # Takes care of division by scalars at least

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


class Add(_Operation, _MathEnabled):
    """docstring for Add"""
    _format = '{} + {}'
    _priority = 1

    def _evaluate(self, a, b):
        return a + b


class Sub(_Operation, _MathEnabled):
    """docstring for Sub"""
    _format = '{} - {}'
    _priority = 1

    def _evaluate(self, a, b):
        return a - b
        
    
class Mul(_Operation, _MathEnabled):
    """docstring for Mul"""
    
    _format = '{} * {}'
    _priority = 2

    def _evaluate(self, a, b):
        return a * b


class Variable(_MathEnabled):
    """docstring for Variable"""

    _counter = 0

    def _next_counter(self):
        Variable._counter += 1
        return Variable._counter


    def __init__(self, name=None, lb=None, ub=None, domain=DEFAULT_DOMAIN):
        super().__init__()
        self.name = 'x{}'.format(self._next_counter()) if name is None else name
        self.name = rename_namespace(self.name)
        self.lb = lb
        self.ub = ub
        self.domain = domain


    def evaluate(self, replacements=None):
        with ignored(AttributeError):
            return self.value
        with ignored(AttributeError):
            return replacements.get(self, self)
        return self


    def take_value(self, solution):
        self.value = solution[self]


    def __str__(self):
        return self.name


    def __repr__(self):
        return '<{} at {}: {}>'.format(self.__class__.__name__, hex(id(self)), self)


class VariableCollection(object):
    """docstring for VariableCollection"""
    def __init__(self, name=None, **kwargs):
        super().__init__()
        self.name = 'X{}'.format(self._next_counter()) if name is None else name
        self.name = rename_namespace(self.name)
        self._kwargs = kwargs
        self._vars = {}

    _counter = 0

    def _next_counter(self):
        VariableCollection._counter += 1
        return VariableCollection._counter

    def __call__(self, *indices):
        if not indices in self._vars:
            if len(indices) == 1:
                name = '{}({})'.format(self.name, indices[0])
            else:
                name = '{}{}'.format(self.name, indices)
            with namespace(''):
                variable = Variable(name=name, **self._kwargs)
            self._vars[indices] = variable
        return self._vars[indices]


    def __str__(self):
        return self.name


    def __repr__(self):
        return '<{} at {}: {}>'.format(self.__class__.__name__, hex(id(self)), self)


class ConstraintError(Exception): pass


class _ConstraintBase(object):
    """docstring for _ConstraintBase"""
    def __init__(self, desc=None, origin=None):
        super().__init__()
        self.desc = desc
        self.origin = origin

    @property
    def variables(self):
        raise NotImplementedError()


class Constraint(_ConstraintBase):
    """docstring for Constraint"""
    def __init__(self, expr, desc=None, **kwargs):
        super().__init__(desc=desc, **kwargs)
        self.expr = expr

    def __str__(self):
        return str(self.expr)


    @property
    def variables(self):
        return self.expr.variables
    


class _SOS(_ConstraintBase):
    """docstring for _SOS"""
    def __init__(self, level, variables, **kwargs):
        super().__init__(**kwargs)
        if not (isinstance(variables, tuple) or isinstance(variables, list)):
            raise ConstraintError('variables must be a tuple or list')
        self._variables = tuple(variables)
        self._level = level

    @property
    def level(self):
        return self._level
    

    def __str__(self):
        return 'SOS{}{}'.format(self._level, self._variables)

    @property
    def variables(self):
        return self._variables


class SOS1(_SOS):
    """docstring for SOS1"""
    def __init__(self, variables, **kwargs):
        super().__init__(1, variables, **kwargs)


class SOS2(_SOS):
    """docstring for SOS2"""
    def __init__(self, variables, **kwargs):
        super().__init__(2, variables, **kwargs)


class _Objective(object):
    """docstring for _Objective"""
    def __init__(self, expr):
        super().__init__()
        self.expr = expr

    @property
    def variables(self):
        return self.expr.variables
    

class Maximize(_Objective):
    """docstring for Maximize"""
    pass

class Minimize(_Objective):
    """docstring for Minimize"""
    pass

class Problem(object):
    """An optimization problem"""
    def __init__(self, constraints=None, objective=None):
        super().__init__()
        self._constraints = set() if constraints is None else constraints
        self.objective = objective

    def _add_constraint(self, constraint):
        if isinstance(constraint, Relation):
            constraint = Constraint(constraint, 'Ad hoc constraint')
        if not isinstance(constraint, (Constraint, _SOS)):
            raise ValueError('{} is not a valid constraint'.format(constraint))
        self._constraints.add(constraint)

    def add(self, constraints):
        try:
            constraints = iter(constraints)
        except TypeError: # not iterable
            constraints = (constraints,)
    
        for c in constraints:
            self._add_constraint(c)
    

    @property
    def variables(self):
        sources = set(self.constraints) | {self.objective}
        return set(chain(*(src.variables for src in sources)))

    @property
    def constraints(self):
        return self._constraints

    def solve(self):
        """Try to solve the optimization problem"""
        raise NotImplementedError()
