# -*- coding: utf-8 -*-

from friendlysam.log import get_logger
from friendlysam.optimization import (
    Solver, SolverError, SolverNotAvailableError, Sense, RelConstraint, SOS1Constraint, SOS2Constraint)
logger = get_logger(__name__)

#from pyomo.environ import *
import pyomo.environ
from pyomo.opt import SolverFactory

import operator

import sympy
from enum import Enum

class PyomoExpressionError(Exception): pass

class PyomoSolver(Solver):

    """docstring for PyomoSolver"""
    def __init__(self):
        """Create a new solver instance

        Raises:
            SolverNotAvailableError if the solver is not available.
        """
        super(PyomoSolver, self).__init__()
        #self._solver = SolverFactory("gurobi", solver_io="python")
        self._solver = SolverFactory("cbc")


    def _add_var(self):
        self._var_counter += 1
        name = 'v{}'.format(self._var_counter)
        var = pyomo.environ.Var()
        setattr(self._model, name, var)
        return var

    def _get_constraint_name(self):
        self._constraint_counter += 1
        return 'c{}'.format(self._constraint_counter)


    def solve(self, problem):
        self._constraint_counter = 0
        self._var_counter = 0
        self._model = pyomo.environ.ConcreteModel()
        
        self._pyomo_variables = {v: self._add_var() for v in problem.variables}

        self._set_objective(problem)

        map(self._add_constraint, problem.constraints)

        self._model.preprocess()

        result = self._solver.solve(self._model)

        if not result.Solution.Status == pyomo.opt.SolutionStatus.optimal:
            raise SolverError("pyomo solution status is '{0}'".format(result.Solution.Status))

        self._model.load(result)

        return {key: variable.value for key, variable in self._pyomo_variables.items()}

    def _add_constraint(self, c):
        if isinstance(c, RelConstraint):
            c = c.expr

        if isinstance(c, sympy.Rel):
            expr = self._make_pyomo_expr(c)
            setattr(self._model, self._get_constraint_name(), pyomo.environ.Constraint(expr=expr))

        elif isinstance(c, SOS1Constraint):
            raise NotImplementedError()

        elif isinstance(c, SOS2Constraint):
            raise NotImplementedError()

        else:
            raise NotImplementedError()

    def _set_objective(self, problem):
        sense_translation = {
            Sense.minimize: pyomo.environ.minimize,
            Sense.maximize: pyomo.environ.maximize }
        expr = self._make_pyomo_expr(problem.objective)
        self._model.obj = pyomo.environ.Objective(expr=expr, sense=sense_translation[problem.sense])

    def _make_pyomo_expr(self, expr):
        symbols = sorted(expr.atoms(sympy.Symbol), key=lambda x: sympy.default_sort_key(x, 'lex'))

        variables = [self._pyomo_variables[s] for s in symbols]

        if len(symbols) == 0:
            return float(expr)

        elif expr.is_polynomial(*symbols):
            polynomial = sympy.Poly(expr, *symbols)
            terms = []

            for exponents, coeff in polynomial.terms():
                coeff = float(coeff)
                if all((e == 0 for e in exponents)):
                    terms.append(coeff)
                else:
                    factors = []
                    for base, exponent in filter(lambda (a, e): e != 0, zip(variables, exponents)):
                        factors.extend([base] * exponent)
                    terms.append(coeff * reduce(operator.mul, factors))
            return sum(terms)

        elif isinstance(expr, sympy.GreaterThan):
            a, b = expr.args
            return self._make_pyomo_expr(a) >= self._make_pyomo_expr(b)

        elif isinstance(expr, sympy.LessThan):
            a, b = expr.args
            return self._make_pyomo_expr(a) <= self._make_pyomo_expr(b)

        elif isinstance(expr, sympy.Equality):
            a, b = expr.args
            return self._make_pyomo_expr(a) == self._make_pyomo_expr(b)

        elif isinstance(expr, sympy.StrictGreaterThan) or isinstance(expr, sympy.StrictLessThan):
            raise PyomoExpressionError('Strict inequalities are not allowed.')

        else:
            raise PyomoExpressionError(
                'Expression "{}" ({}) cannot be translated.'.format(expr, type(expr)))
