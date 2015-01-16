# -*- coding: utf-8 -*-

from friendlysam.log import get_logger
logger = get_logger(__name__)

import operator
import collections

import pyomo.environ as pyoenv
import pyomo.opt
from pyomo.opt import SolverFactory

from friendlysam.optimization.core import *

DEFAULT_OPTIONS = dict(
    solver_order=[
        dict(name='gurobi', solver_io='python'),
        dict(name='cbc', solver_io='nl')
    ])

    
class PyomoEngine(object):
    """docstring for PyomoEngine"""
    _domain_mapping = {
        Domain.real: pyoenv.Reals,
        Domain.integer: pyoenv.Integers,
        Domain.binary: pyoenv.Binary,
        None: None
    }

    def __init__(self):
        super(PyomoEngine, self).__init__()
        self.options = DEFAULT_OPTIONS
        self._names = set()
        self._var_name_counter = 0
        self._variables = {}

    def _register_unique_name(self, name):
        if name is not None:
            if name in self._names:
                raise ValueError('a variable named {} already exists'.format(name))
            elif name == '':
                raise ValueError('empty string is not an allowed variable name')
            elif not isinstance(name, str):
                raise ValueError('variable name should be a string')

        while name is None or name in self._names:
            self._var_name_counter += 1
            name = 'x{}'.format(self._var_name_counter)

        self._names.add(name)
        return name


    def register(self, owner, options_func):
        self._options_funcs[owner] = options_func

    def get_variable(self, variable, index):
        if not (variable, index) in self._variables:
            options = dict(
                lb=variable.lb,
                ub=variable.ub,
                domain=variable.domain,
                name=variable.name)

            for key, value in options.items():
                if callable(value):
                    options[key] = value(index)

            name = self._register_unique_name(options.pop('name'))

            options['domain'] = self._domain_mapping[options['domain']]
            options['bounds'] = (options['lb'], options['ub'])
            del options['lb']
            del options['ub']

            symbol = pyoenv.Var(**options)
            symbol.name = name
            symbol._friendlysam_index = (variable, index)

            self._variables[variable, index] = symbol

        return self._variables[variable, index]

    def variables(self):
        return self._variables.values()

    def delete_variable(self, variable, index):
        try:
            del self._variables[variable, index]
        except KeyError:
            pass

    def problem(self, **kwargs):
        if 'engine' in kwargs:
            raise RuntimeError('Engine is implicitly specified already.')
        kwargs['engine'] = self
        return PyomoProblem(**kwargs)


class PyomoProblem(Problem):
    """docstring for PyomoProblem"""

    def _get_and_apply_solver(self, problem):
        solver_order = self.engine.options['solver_order']

        for solver in solver_order:
            exceptions = []
            try:
                solver = SolverFactory(solver['name'], solver_io=solver['solver_io'])
                return solver.solve(problem)
            except Exception, e:
                exceptions.append({'solver': solver, 'exception': str(e)})

        raise RuntimeError('None of the solvers worked. More info: {}'.format(exceptions))

    def solve(self):        
        model = pyoenv.ConcreteModel()

        for v in self.engine.variables():
            setattr(model, v.name, v)

        for i, c in enumerate(self.constraints):
            if isinstance(c, Constraint):
                setattr(model, 'c{}'.format(i), pyoenv.Constraint(expr=c.expr))
                
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
        model.objective = pyoenv.Objective(expr=self.objective.expr, sense=sense)

        model.preprocess()

        result = self._get_and_apply_solver(model)

        if not result.Solution.Status == pyomo.opt.SolutionStatus.optimal:
            raise SolverError("pyomo solution status is '{0}'".format(result.Solution.Status))

        model.load(result)

        return {v._friendlysam_index: v.value for v in self.engine.variables()}


