# -*- coding: utf-8 -*-

from friendlysam.log import get_logger
logger = get_logger(__name__)

import sympy
from enum import Enum


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

    def symbol_collection(self, name=None):
        name = self._unique_name(name)
        collection = LazyIndexedFunction(lambda idx: self.symbol('{}({})'.format(name, idx)))
        return collection

def make_constraints(symbols, lb=None, ub=None, sos1=False, sos2=False):
    try:
        symbols = tuple(symbols)
    except TypeError: # symbols was not iterable
        symbols = (symbols, )

    constraints = set()
    if lb is not None:
        constraints.update(lb <= s for s in symbols)
    if ub is not None:
        constraints.update(s <= ub for s in symbols)

    if sos1:
        constraints.add(SOS1Constraint(symbols))

    if sos2:
        constraints.add(SOS2Constraint(symbols))

    return constraints


class ConstraintError(Exception): pass


class Constraint(object): pass


class RelConstraint(Constraint):
    """docstring for RelConstraint"""
    def __init__(self, expr):
        super(RelConstraint, self).__init__()
        if isinstance(expr, sympy.Basic):
            self._expr = expr
        else:
            raise ConstraintError('{} is not a sympy Basic object'.format(expr))

    def __str__(self):
        return str(self._expr)

    @property
    def expr(self):
        return self._expr

    def simplify(self, rules):
        replaced = self.expr.xreplace(rules)
        if replaced == self.expr:
            return None
        else:
            return (RelConstraint(replaced),), {}



class SOS1Constraint(Constraint):
    """docstring for SOS1Constraint"""
    def __init__(self, symbols):
        super(SOS1Constraint, self).__init__()
        self._symbols = set(symbols)

    def __str__(self):
        return 'SOS1{}'.format(tuple(self._symbols))

    @property
    def symbols(self):
        return self._symbols

    def simplify(self, rule):
        not_replaced = set(filter(
            lambda r: isinstance(r, sympy.Basic),
            (s.xreplace(rule) for s in self._symbols)))
        replaced = self._symbols - not_replaced
        if len(replaced) == 0:
            return None
        elif len(replaced) == 1:
            return (), {s: 0 for s in not_replaced}
        else:
            return (False,), {}


class SOS2Constraint(Constraint):
    """docstring for SOS2Constraint"""
    def __init__(self, symbols):
        super(SOS2Constraint, self).__init__()
        if not isinstance(symbols, tuple) or isinstance(symbols, list):
            raise ConstraintError('symbols must be a tuple or list')
        self._symbols = tuple(symbols)

    def __str__(self):
        return 'SOS2{}'.format(self._symbols)

    @property
    def symbols(self):
        return self._symbols


class LazyIndexedFunction(object):
    """docstring for LazyIndexedFunction"""
    def __init__(self, func):
        super(LazyIndexedFunction, self).__init__()
        self._func = func
        self._items = {}

    def __getitem__(self, index):
        if not index in self._items:
            self._items[index] = self._func(index)
        return self._items[index]


class Sense(Enum):
    """The sense of an optimization objective"""
    minimize = 1
    maximize = 2
        

class Problem(object):
    """An optimization problem"""
    def __init__(self):
        super(Problem, self).__init__()
        self.sense = Sense.minimize
        self._constraints = set()
        self.rules = {}
        self.objective = None
        self.solver = None

    @property
    def constraints(self):
        return self._constraints

    def add_constraints(self, constraints):
        for c in constraints:
            if isinstance(c, sympy.Rel):
                c = RelConstraint(c)
            if not isinstance(c, Constraint):
                raise ConstraintError('{} is not a valid constraint'.format(c))
            self._constraints.add(c)

    @property
    def variables(self):
        expressions = set(filter(lambda c: isinstance(c, sympy.Rel), self._constraints))
        expressions.add(self.objective)
        symbols = set()
        for e in expressions:
            symbols.update(e.atoms(sympy.Symbol))
        return symbols

    def simplify(self):
        changed = False
        logger.debug('Simplifying...')
        new_constraints = set()
        new_rules = {}
        for c in self._constraints:
            simplification = c.simplify(self.rules)
            if simplification is None:
                continue
            else:
                changed = True
                new_constraints, new_rules = simplification
                logger.debug('{} --> {}, {}'.format(
                    c,
                    '(' + ', '.join(str(c) for c in new_constraints) + ')',
                    new_rules))
                self._constraints.remove(c)
                self._constraints.update(new_constraints)
                self.rules.update(new_rules)

        self._constraints.discard(True)
        self._constraints.discard(sympy.true)

        if changed:
            self.simplify()


    def solve(self):
        """Try to solve the optimization problem"""

        if False in self._constraints or sympy.false in self._constraints:
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
