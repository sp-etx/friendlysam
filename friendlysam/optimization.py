# -*- coding: utf-8 -*-

import sympy
import gurobipy
import operator
from enum import Enum

class VariableError(Exception): pass

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class VariableFactory(object):
    __metaclass__ = Singleton

    def __init__(self):
        super(VariableFactory, self).__init__()
        self._names = set()
        self._counter = 0

    def _unique_name(self, name):
        if name is not None:
            if name in self._names:
                raise VariableError('a variable named {} already exists'.format(name))
            elif name == '':
                raise VariableError('empty string is not an allowed variable name')
            elif not isinstance(name, str):
                raise VariableError('variable name should be a string')

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



class SOS1Constraint(object):
    """docstring for SOS1Constraint"""
    def __init__(self, symbols):
        super(SOS1Constraint, self).__init__()
        self._symbols = symbols

    @property
    def symbols(self):
        return self._symbols


class SOS2Constraint(object):
    """docstring for SOS2Constraint"""
    def __init__(self, symbols):
        super(SOS2Constraint, self).__init__()
        self._symbols = symbols

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
        self._solution = self.solver.solve(self)

    def evaluate(self, expr):
        """Evaluate an expression in the optimal point of the optimization problem"""
        raise NotImplementedError()

class Solver(object):
    """Base class for optimization solvers"""
        
    def solve(self, problem):
        """Solve an optimization problem and return the solution

        Args:
            problem (Problem): The optimization problem to solve.

        Returns:
            A dict `{variable: value for variable in problem.variables}`
        """
        raise NotImplementedError()

        
class GurobiExpressionError(Exception): pass

class GurobiSolver(object):
    """docstring for GurobiSolver"""
    def __init__(self):
        super(GurobiSolver, self).__init__()

    def solve(self, problem):
        self._model = gurobipy.Model("my model")
        self._gurobi_variables = {v: self._model.addVar() for v in problem.variables}
        self._model.update()

        self._set_objective(problem)
        
        map(self._add_constraint, problem.constraints)

        self._model.optimize()

        return {key: value.x for key, value in self._gurobi_variables.items()}

    def _add_constraint(self, c):
        if isinstance(c, sympy.Rel):
            print('Constraint', c)
            self._model.addConstr(self._make_gurobi_expr(c))

        elif isinstance(c, SOS1Constraint):
            variables = [self._gurobi_variables[symbol] for symbol in c.symbols]
            print('SOS1 group', c.symbols, variables)
            self._model.addSOS(gurobipy.GRB.SOS_TYPE1, variables)

        elif isinstance(c, SOS2Constraint):
            variables = [self._gurobi_variables[symbol] for symbol in c.symbols]
            order = [i + 1 for i in range(len(variables))]
            print('SOS2 group', c.symbols, variables)
            self._model.addSOS(gurobipy.GRB.SOS_TYPE2, variables, order)


    def _set_objective(self, problem):
        sense_translation = {
            Sense.minimize: gurobipy.GRB.MINIMIZE,
            Sense.maximize: gurobipy.GRB.MAXIMIZE }

        self._model.setObjective(
            self._make_gurobi_expr(problem.objective),
            sense=sense_translation[problem.sense])

    def _get_variable(self, symbol):
        if not symbol in self._gurobi_variables:
            self._gurobi_variables[symbol] = self._model.addVar(name=symbol.name)
            self._model.update()
        return self._gurobi_variables[symbol]

    def _make_gurobi_expr(self, expr):
        symbols = sorted(expr.atoms(sympy.Symbol), key=lambda x: sympy.default_sort_key(x, 'lex'))

        variables = [self._gurobi_variables[s] for s in symbols]

        if len(symbols) == 0:
            return expr

        elif expr.is_polynomial(*symbols):
            polynomial = sympy.Poly(expr, *symbols)
            if polynomial.is_linear:
                gurobi_expr = gurobipy.LinExpr()
            elif polynomial.is_quadratic:
                gurobi_expr = gurobipy.QuadExpr()
            else:
                raise GurobiExpressionError("The degree of polynomial {} is not supported.")

            for exponents, coeff in polynomial.terms():
                if all((e == 0 for e in exponents)):
                    gurobi_expr.addConstant(coeff)
                else:
                    factors = []
                    for base, exponent in filter(lambda (a, e): e != 0, zip(variables, exponents)):
                        factors.extend([base] * exponent)
                    gurobi_expr.add(reduce(operator.mul, factors), coeff)
            return gurobi_expr

        elif isinstance(expr, sympy.GreaterThan):
            a, b = expr.args
            return self._make_gurobi_expr(a) >= self._make_gurobi_expr(b)

        elif isinstance(expr, sympy.LessThan):
            a, b = expr.args
            return self._make_gurobi_expr(a) <= self._make_gurobi_expr(b)

        elif isinstance(expr, sympy.Equality):
            a, b = expr.args
            return self._make_gurobi_expr(a) == self._make_gurobi_expr(b)

        elif isinstance(expr, sympy.StrictGreaterThan) or isinstance(expr, sympy.StrictLessThan):
            raise GurobiExpressionError('Strict inequalities are not allowed.')

        else:
            raise GurobiExpressionError(
                'Expression "{}" ({}) cannot be translated.'.format(expr, type(expr)))


import random
import time


if __name__ == '__main__':
    
    p = Problem()
    x, y, z = sympy.symbols('x y z')
    p.constraints.add(x - y*y >= 3)
    p.objective = x + 0.5*y
    p.solver = GurobiSolver()
    p.solve()
    print(p._solution)
    # t0 = time.time()
    # m = gurobipy.Model('aoeu')
    # qe = gurobipy.QuadExpr()

    # N = 1
    # gvars = [m.addVar(name='x'+str(n)) for n in range(N)]
    # m.update()
    
    # for i in range(1):
    #     x = gvars[:]
    #     y = gvars[:]
    #     random.shuffle(x)
    #     random.shuffle(y)
    #     qe.addTerms(list(range(2,N+2)), x, y)
    #     print(qe == 0)
    #     m.addConstr(qe)
    #     m.update()
    #     m.setObjective(x[0]+3)
    #     m.optimize()
    #     for c in m.getQConstrs():
    #         print(c)
    #     print(m.getQConstrs(), m.getConstrs())

    # print(time.time()-t0)
