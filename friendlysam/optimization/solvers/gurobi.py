# -*- coding: utf-8 -*-

from friendlysam.log import get_logger
from friendlysam.optimization import Solver, SolverError, SolverNotAvailableError, Sense
logger = get_logger(__name__)

import operator

import sympy
from enum import Enum

try:
    import gurobipy
except Exception, e:
    no_gurobi = e.message


# gurobipy.GRB.LOADED (1)
# Model is loaded, but no solution information is available.

# gurobipy.GRB.OPTIMAL (2)
# Model was solved to optimality (subject to tolerances), and an optimal solution is available.

# gurobipy.GRB.INFEASIBLE (3)
# Model was proven to be infeasible.

# gurobipy.GRB.INF_OR_UNBD (4)
# Model was proven to be either infeasible or unbounded. To obtain a more definitive conclusion,
# set the DualReductions parameter to 0 and reoptimize.

# gurobipy.GRB.UNBOUNDED (5)
# Model was proven to be unbounded. Important note: an unbounded status indicates the presence of
# an unbounded ray that allows the objective to improve without limit. It says nothing about
# whether the model has a feasible solution. If you require information on feasibility, you should
# set the objective to zero and reoptimize.

# gurobipy.GRB.CUTOFF (6)
# Optimal objective for model was proven to be worse than the value specified in the Cutoff
# parameter. No solution information is available.

# gurobipy.GRB.ITERATION_LIMIT (7)
# Optimization terminated because the total number of simplex iterations performed exceeded the
# value specified in the IterationLimit parameter, or because the total number of barrier
# iterations exceeded the value specified in the BarIterLimit parameter.

# gurobipy.GRB.NODE_LIMIT (8)
# Optimization terminated because the total number of branch-and-cut nodes explored exceeded the
# value specified in the NodeLimit parameter.

# gurobipy.GRB.TIME_LIMIT (9)
# Optimization terminated because the time expended exceeded the value specified in the TimeLimit
# parameter.

# gurobipy.GRB.SOLUTION_LIMIT (10)
# Optimization terminated because the number of solutions found reached the value specified in the
# SolutionLimit parameter.

# gurobipy.GRB.INTERRUPTED (11)
# Optimization was terminated by the user.

# gurobipy.GRB.NUMERIC (12)
# Optimization was terminated due to unrecoverable numerical difficulties.

# gurobipy.GRB.SUBOPTIMAL (13)
# Unable to satisfy optimality tolerances; a sub-optimal solution is available.

# gurobipy.GRB.IN_PROGRESS (14)
# A non-blocking optimization call was made (by setting the NonBlocking parameter to 1 in a Gurobi
# Compute Server environment), but the associated optimization run is not yet complete.

class GurobiExpressionError(Exception): pass

class GurobiSolver(Solver):

    """docstring for GurobiSolver"""
    def __init__(self):
        """Create a new solver instance

        Raises:
            SolverNotAvailableError if the solver is not available.
        """
        super(GurobiSolver, self).__init__()

        try:
            gurobipy
        except NameError:
            raise SolverNotAvailableError('cannot use GurobiSolver ({})'.format(no_gurobi))


    def solve(self, problem):
        self._model = gurobipy.Model("my model")
        self._gurobi_variables = {v: self._model.addVar() for v in problem.variables}
        self._model.update()

        self._set_objective(problem)
        
        map(self._add_constraint, problem.constraints)

        self._model.optimize()

        if not self._model.status == gurobipy.GRB.OPTIMAL:
            raise SolverError('gurobi status is {0}'.format(self._model.status))

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
