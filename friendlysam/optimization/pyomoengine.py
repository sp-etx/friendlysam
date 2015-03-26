# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import super
from builtins import dict
from builtins import str
from future import standard_library
standard_library.install_aliases()
from friendlysam.log import get_logger
logger = get_logger(__name__)

import operator
import collections
from itertools import chain

import pyomo.environ as pyoenv
import pyomo.opt
from pyomo.opt import SolverFactory

from friendlysam.optimization import (
    Problem, Variable, Constraint, SOS1, SOS2, Maximize, Minimize, Domain)

DEFAULT_OPTIONS = dict(
    solver_order=[
        dict(name='gurobi', solver_io='python'),
        dict(name='cbc', solver_io='nl')
    ])

class PyomoProblem(Problem):
    """docstring for PyomoProblem"""
    _domain_mapping = {
        Domain.real: pyoenv.Reals,
        Domain.integer: pyoenv.Integers,
        Domain.binary: pyoenv.Binary,
        None: None
    }

    def __init__(self):
        super(PyomoProblem, self).__init__()
        self.options = DEFAULT_OPTIONS
        self._names = set()

    def _get_unique_name(self, name=None):
        _counter = 0
        while name is None or name in self._names:
            _counter += 1
            name = 'x{}'.format(_counter)

        self._names.add(name)
        return name

    def _make_pyomo_var(self, variable):
        options = dict(
            bounds=(variable.lb, variable.ub),
            domain=self._domain_mapping[variable.domain])

        name = self._get_unique_name(variable.name)

        pyovar = pyoenv.Var(**options)
        pyovar.name = name

        return pyovar

    def _variables_without_value(self):
        leaves = chain(self.objective.expr.leaves, *(c.expr.leaves for c in self.constraints))
        return (l for l in leaves if isinstance(l, Variable) and not hasattr(l, 'value'))

    def solve(self):        
        model = pyoenv.ConcreteModel()
        pyomo_variables = {v: self._make_pyomo_var(v) for v in self._variables_without_value()}
        for v in pyomo_variables.values():
            setattr(model, v.name, v)

        for i, c in enumerate(self.constraints):
            if isinstance(c, Constraint):
                setattr(model,
                    'c{}'.format(i),
                    pyoenv.Constraint(expr=c.expr.evaluate(replacements=pyomo_variables)))
                
            elif isinstance(c, SOS1):
                raise NotImplementedError()

            elif isinstance(c, SOS2):
                raise NotImplementedError()

            else:
                raise NotImplementedError('Cannot handle constraint {}'.format(c))

        if isinstance(self.objective, Minimize):
            sense = pyoenv.minimize
        elif isinstance(self.objective, Maximize):
            sense = pyoenv.maximize
        model.objective = pyoenv.Objective(
            expr=self.objective.expr.evaluate(replacements=pyomo_variables), sense=sense)

        model.preprocess()

        result = self._get_and_apply_solver(model)

        if not result.Solution.Status == pyomo.opt.SolutionStatus.optimal:
            raise SolverError("pyomo solution status is '{0}'".format(result.Solution.Status))

        model.load(result)

        return {v: pv.value for v, pv in pyomo_variables.items()}

    def _get_and_apply_solver(self, problem):
        solver_order = self.options['solver_order']

        for solver in solver_order:
            exceptions = []
            try:
                solver = SolverFactory(solver['name'], solver_io=solver['solver_io'])
                return solver.solve(problem)
            except Exception as e:
                exceptions.append({'solver': solver, 'exception': str(e)})

        raise RuntimeError('None of the solvers worked. More info: {}'.format(exceptions))

