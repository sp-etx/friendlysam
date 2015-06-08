# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import operator
import collections
from itertools import chain

from pulp import *

import friendlysam as fs
from friendlysam import SolverError, ConstraintError


def _cbc_solve(problem):
    solver = PULP_CBC_CMD()
    return solver.solve_CBC(problem, use_mps=False)

DEFAULT_OPTIONS = dict(
    solver_funcs=[
        _cbc_solve,
        GUROBI_CMD(msg=0).solve
    ])

_domain_mapping = {
    fs.Domain.real: LpContinuous,
    fs.Domain.integer: LpInteger,
    fs.Domain.binary: LpBinary,
    None: None
}

_pulp_statuses = {
    LpStatusNotSolved: 'LpStatusNotSolved',
    LpStatusOptimal: 'LpStatusOptimal',
    LpStatusInfeasible: 'LpStatusInfeasible',
    LpStatusUnbounded: 'LpStatusUnbounded',
    LpStatusUndefined: 'LpStatusUndefined'
}

class PulpSolver(object):
    """docstring for PulpSolver"""

    def __init__(self, options):
        super().__init__()
        self.options = DEFAULT_OPTIONS.copy()
        self.options.update(options)
        self._last_problem_vars = {}
        self._last_problem_expressions = {}
        self._var_counter = 0

    def __getstate__(self):
        return self.options

    def __setstate__(self, options):
        self.__init__(options)



    def _make_pulp_var(self, variable):
        options = dict(
            lowBound=variable.lb,
            upBound=variable.ub,
            cat=_domain_mapping[variable.domain])

        name = 'x{}'.format(self._var_counter)
        self._var_counter += 1

        return LpVariable(name, **options)

    _evaluators = fs.CONCRETE_EVALUATORS.copy()
    _evaluators[fs.Sum] = lambda *x: pulp.lpSum(x)


    def solve(self, problem):
        expressions = {}
        cached_expressions = self._last_problem_expressions
        def evaluate(expr):
            if any(hasattr(v, 'value') for v in expr.variables):
                expressions[expr] = expr.evaluate(replace=pulp_vars, evaluators=self._evaluators)
            else:
                try:
                    evaluated = expressions[expr] = cached_expressions[expr]
                except KeyError:
                    expressions[expr] = expr.evaluate(replace=pulp_vars, evaluators=self._evaluators)
            return expressions[expr]

        cached_vars = self._last_problem_vars
        pulp_vars = {}
        for v in problem.variables_without_value():
            try:
                pulp_vars[v] = cached_vars[v]
            except KeyError:
                pulp_vars[v] = self._make_pulp_var(v)
        self._last_problem_vars = pulp_vars

        if isinstance(problem.objective, fs.Minimize):
            sense = LpMinimize
        elif isinstance(problem.objective, fs.Maximize):
            sense = LpMaximize
        else:
            raise RuntimeError('Unexpected objective {}'.format(problem.objective))

        model = LpProblem('friendlysam', sense)
        
        model += evaluate(problem.objective.expr)

        for i, c in enumerate(problem.constraints):
            if isinstance(c, fs.Constraint):
                try:
                    expr = evaluate(c.expr)
                    if type(expr) == bool: # Because __eq__ is overloaded on pulp expressions
                        if expr == True:
                            continue
                        else:
                            msg = ('The expression in {} evaluates to False, '
                                'so the problem is infeasible.').format(c)
                            raise ConstraintError(msg, constraint=c)
                    model += expr
                except Exception:
                    if isinstance(expr, fs.Less):
                        msg = 'Strict inequalities are not supported by this solver: {}'.format(c)
                        raise ConstraintError(msg, constraint=c) from e
                    raise

            elif isinstance(c, (fs.SOS1, fs.SOS2)):
                if isinstance(c, fs.SOS1):
                    sosdict = model.sos1
                elif isinstance(c, fs.SOS2):
                    sosdict = model.sos2
                else:
                    raise NotImplementedError()

                weights = list(range(1, len(c.variables)+1))
                constr_name = 'sosconstr{}'.format(i)
                sosdict[constr_name] = {pulp_vars[v]: w for v, w in zip(c.variables, weights)}

            else:
                raise NotImplementedError('Cannot handle constraint {}'.format(c))

        self._last_problem_expressions = expressions

        exceptions = []
        for solver_func in self.options['solver_funcs']:
            try:
                status = solver_func(model)
                break
            except Exception as e:
                exceptions.append({'solver': solver_func, 'exception': str(e)})
        else:
            raise SolverError('None of the solvers worked. More info: {}'.format(exceptions))
        
        if not status == LpStatusOptimal:
            raise fs.SolverError("pulp solution status is '{0}'".format(_pulp_statuses[status]))

        for pv in pulp_vars.values():
            assert pv.value() is not None
        return {v: pv.value() for v, pv in pulp_vars.items()}
