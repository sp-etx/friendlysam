# -*- coding: utf-8 -*-

from friendlysam.log import get_logger
logger = get_logger(__name__)

import sympy
from enum import Enum

from friendlysam.util import Indexed


class SymbolError(Exception): pass

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class SymbolFactory(object):
    __metaclass__ = Singleton

    def __init__(self):
        super(SymbolFactory, self).__init__()
        self._names = set()
        self._counter = 0

    def _unique_name(self, name):
        if name is not None:
            if name in self._names:
                raise SymbolError('a symbol named {} already exists'.format(name))
            elif name == '':
                raise SymbolError('empty string is not an allowed symbol name')
            elif not isinstance(name, str):
                raise SymbolError('symbol name should be a string')

        while name is None or name in self._names:
            self._counter += 1
            name = 'x{}'.format(self._counter)

        self._names.add(name)

        return name

    def symbol(self, name=None):
        name = self._unique_name(name)
        symbol = sympy.Symbol(name)
        return symbol


class Variable(object):
    """docstring for Variable"""
    def __init__(self, name, lb=None, ub=None, integer=False):
        super(Variable, self).__init__()
        self.name = name
        self.lb = lb
        self.ub = ub
        self.integer = integer
        self._symbols = {}


    def __call__(self, index=None):
        if not index in self._symbols:
            if index is None:
                name = self.name
            else:
                name = '{}[{}]'.format(self.name, index)
            self._symbols[index] = SymbolFactory().symbol(name)
        return self._symbols[index]

    def replace_symbols(self, data, indices):
        for idx in indices:
            if idx in self._symbols:
                self._symbols[idx] = self.try_replace(self._symbols[idx], data)
            
    def constraint_func(self, index):
        constraints = set()
        if self.lb is not None:
            constraints.add(self.lb <= self(index))
        if self.ub is not None:
            constraints.add(self(index) <= self.ub)
        if self.integer:
            raise NotImplementedError()
        return constraints

    def try_replace(self, something, data):
        return something.xreplace(data) if isinstance(something, sympy.Basic) else something


class PiecewiseAffineArg(Variable):
    """docstring for Variable"""
    def __init__(self, name, points):
        super(PiecewiseAffineArg, self).__init__(name)
        self.points = points

    def __call__(self, index=None):
        return self.weighted_sum(index)

    def weighted_sum(self, index):
        return sum([point * weight for point, weight in zip(self.points, self.weights(index))])

    def weights(self, index):
        if not index in self._symbols:
            self._symbols[index] = self._make_symbols(index)
        return self._symbols[index]
    

    def _make_symbols(self, index):
        if index is None:
            return [sympy.Symbol('{}_{}'.format(self.name, i)) for i in self.points]
        else:
            return [sympy.Symbol('{}_{}[{}]'.format(self.name, i, index)) for i in self.points]

    def replace_symbols(self, data, indices):
        for idx in indices:
            if idx in self._symbols:
                self._symbols[idx] = [self.try_replace(s, data) for s in self._symbols[idx]]

    def constraint_func(self, index):
        weights = self.weights(index)
        constraints = (
            SOS2Constraint(weights),
            RelConstraint(sympy.Eq(sum(weights), 1))
            )
        return constraints


class ConstraintError(Exception): pass


class RelConstraint(object):
    """docstring for RelConstraint"""
    def __init__(self, expr):
        super(RelConstraint, self).__init__()
        self.expr = expr

    def __str__(self):
        return str(self.expr)


class SOS1Constraint(object):
    """docstring for SOS1Constraint"""
    def __init__(self, symbols):
        super(SOS1Constraint, self).__init__()
        self._symbols = set(symbols)

    def __str__(self):
        return 'SOS1{}'.format(tuple(self._symbols))

    @property
    def symbols(self):
        return self._symbols

class SOS2Constraint(object):
    """docstring for SOS2Constraint"""
    def __init__(self, symbols):
        super(SOS2Constraint, self).__init__()
        if not (isinstance(symbols, tuple) or isinstance(symbols, list)):
            raise ConstraintError('symbols must be a tuple or list')
        self._symbols = tuple(symbols)

    def __str__(self):
        return 'SOS2{}'.format(self._symbols)

    @property
    def symbols(self):
        return self._symbols


class Sense(Enum):
    """The sense of an optimization objective"""
    minimize = 1
    maximize = 2
        

class Problem(object):
    """An optimization problem"""
    def __init__(self):
        super(Problem, self).__init__()
        self.sense = Sense.minimize
        self.constraints = set()
        self.objective = None
        self.solver = None


    @property
    def variables(self):
        expressions = set(filter(lambda c: isinstance(c, sympy.Rel), self.constraints))
        expressions.add(self.objective)
        symbols = set()
        for e in expressions:
            symbols.update(e.atoms(sympy.Symbol))
        return symbols

    def solve(self):
        """Try to solve the optimization problem"""

        self.constraints.discard(True)
        self.constraints.discard(sympy.true)

        if False in self.constraints or sympy.false in self.constraints:
            raise ConstraintError('The problem cannot be solved because some constraint is False.')

        self._solution = self.solver.solve(self)

    def evaluate(self, expr):
        """Evaluate an expression in the optimal point of the optimization problem"""
        raise NotImplementedError()


class SolverNotAvailableError(Exception): pass

class SolverError(Exception): pass

class Solver(object):
    """Base class for optimization solvers

    This base class only defines the interface.
    """

    def __init__(self):
        """Create a new solver instance

        Raises:
            SolverNotAvailableError if the solver is not available.
        """
        super(Solver, self).__init__()

        
    def solve(self, problem):
        """Solve an optimization problem and return the solution

        Args:
            problem (Problem): The optimization problem to solve.

        Returns:
            A dict `{variable: value for variable in problem.variables}`

        Raises:
            SolverError if problem could not be solved.
        """
        raise NotImplementedError()


# import random
# import time


# if __name__ == '__main__':
    
#     p = Problem()
#     x, y, z = sympy.symbols('x y z')
#     p.constraints.add(x - y*y >= 3)
#     p.objective = x + 0.5*y
#     p.solver = GurobiSolver()
#     p.solve()
#     print(p._solution)
#     # t0 = time.time()
#     # m = gurobipy.Model('aoeu')
#     # qe = gurobipy.QuadExpr()

#     # N = 1
#     # gvars = [m.addVar(name='x'+str(n)) for n in range(N)]
#     # m.update()
    
#     # for i in range(1):
#     #     x = gvars[:]
#     #     y = gvars[:]
#     #     random.shuffle(x)
#     #     random.shuffle(y)
#     #     qe.addTerms(list(range(2,N+2)), x, y)
#     #     print(qe == 0)
#     #     m.addConstr(qe)
#     #     m.update()
#     #     m.setObjective(x[0]+3)
#     #     m.optimize()
#     #     for c in m.getQConstrs():
#     #         print(c)
#     #     print(m.getQConstrs(), m.getConstrs())

#     # print(time.time()-t0)
