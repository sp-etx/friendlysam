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

from itertools import chain
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

    _counter = 0
    def __init__(self, name=None, lb=None, ub=None, domain=DEFAULT_DOMAIN):
        super().__init__()
        self._counter += 1
        self._name = 'x{}'.format(self._counter) if name is None else name
        self.lb = lb
        self.ub = ub
        self.domain = domain
        self.constraints = set()

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
        return tuple(l for l in self.expr.leaves if isinstance(l, Variable))
    


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
        return tuple(l for l in self.expr.leaves if isinstance(l, Variable))
    

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
        self._variables = tuple(self._make_variable(p) for p in points)
        self._arg = self.func(self._points)

        constraints = ({
            SOS2(self._variables, desc='PiecewiseAffine variables'),
            Constraint(sum(self._variables) == 1, desc='PiecewiseAffine sum')} | 
            {Constraint(w >= 0, 'Nonnegative weight in PiecewiseAffine')
             for w in self._variables})

        for variable in self._variables:
            variable.constraints = constraints


    @property
    def variables(self):
        return self._variables


    @property
    def points(self):
        return self._points


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
        return sum(val * variable for val, variable in zip(values, self._variables))


class Problem(object):
    """An optimization problem"""
    def __init__(self, constraints=None, objective=None):
        super().__init__()
        self._constraints = set() if constraints is None else constraints
        self.objective = objective

    def add_constraint(self, constraints):
        self._constraints.add(constraints)

    def update_constraints(self, constraints):
        self._constraints.update(constraints)

    @property
    def variables(self):
        sources = set((self.objective,)) | self.constraints
        return frozenset(chain(*(source.variables for source in sources)))

    @property
    def constraints(self):
        all_constraints = set()

        # Begin with the explicitly added constraints AND any constraints that come with
        # the variables of the objective function.
        new_constraints = set(self._constraints)
        new_constraints.update(chain(*(v.constraints for v in self.objective.variables)))

        # Then add constraints that come variables used in these constraints.
        # Search through variables' constraints, etc, until no more are found.
        while len(new_constraints) > 0:
            all_constraints.update(new_constraints)
            variables = chain(*(c.variables for c in new_constraints))
            potentially_new_constraints = set(chain(*(v.constraints for v in variables)))
            new_constraints = potentially_new_constraints - all_constraints
        return frozenset(all_constraints)

    def solve(self):
        """Try to solve the optimization problem"""
        raise NotImplementedError()
