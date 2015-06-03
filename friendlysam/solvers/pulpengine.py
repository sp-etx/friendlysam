# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import operator
import collections
from itertools import chain

from pulp import *

import friendlysam as fs
from friendlysam import SolverError


def _cbc_solve(problem):
    solver = PULP_CBC_CMD()
    return solver.solve_CBC(problem, use_mps=False)

DEFAULT_OPTIONS = dict(
    solver_funcs=[
        GUROBI_CMD(msg=0).solve,
        _cbc_solve
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

    def __init__(self, **kwargs):
        super().__init__()
        self.options = DEFAULT_OPTIONS.copy()
        self.options.update(kwargs)
        self._var_cache = {}
        self._expr_cache = {}
        self._var_counter = 0

    def _make_pulp_var(self, variable):
        options = dict(
            lowBound=variable.lb,
            upBound=variable.ub,
            cat=_domain_mapping[variable.domain])

        name = 'x{}'.format(self._var_counter)
        self._var_counter += 1

        return LpVariable(name, **options)

    _evaluators = fs.get_concrete_evaluators()
    _evaluators[fs.Sum] = lambda *x: pulp.lpSum(x)

    def solve(self, problem):
        vc = self._var_cache
        ec = self._expr_cache
        pulp_vars = {}
        expressions = {}
        for v in problem.variables_without_value():
            try:
                pulp_vars[v] = vc[v]
            except KeyError:
                pulp_vars[v] = self._make_pulp_var(v)
        self.reu = 0
        self.tot = 0
        def evaluate(expr):
            self.tot += 1
            if any(hasattr(v, 'value') for v in expr.variables):
                expr = expr.evaluate()
            try:
                expressions[expr] = ec[expr]
                self.reu += 1
            except KeyError:
                expressions[expr] = expr.evaluate(replace=pulp_vars, evaluators=self._evaluators)
            return expressions[expr]
        #pulp_vars = {v: self._make_pulp_var(v) for v in problem.variables}
        self._var_cache = pulp_vars

        if isinstance(problem.objective, fs.Minimize):
            sense = LpMinimize
        elif isinstance(problem.objective, fs.Maximize):
            sense = LpMaximize
        model = LpProblem('friendlysam', sense)
        
        model += evaluate(problem.objective.expr)

        for i, c in enumerate(problem.constraints):
            if isinstance(c, fs.Constraint):
                try:
                    model += evaluate(c.expr)
                except Exception:
                    if isinstance(expr, (fs.Greater, fs.Less)):
                        msg = 'Strict inequalities are not supported by this solver: {}'.format(
                            c)
                        raise SolverError(msg) from e
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

        self._expr_cache = expressions

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

        logger.info('reused {}'.format(self.reu/self.tot))

        for pv in pulp_vars.values():
            assert pv.value() is not None
        return {v: pv.value() for v, pv in pulp_vars.items()}
