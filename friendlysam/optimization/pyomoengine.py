# -*- coding: utf-8 -*-

from friendlysam.log import get_logger
logger = get_logger(__name__)

import operator
import collections

import pyomo.environ as pyoenv
import pyomo.opt
from pyomo.opt import SolverFactory

from friendlysam.misc import Singleton
from friendlysam.optimization.optimization import Domain, Constraint, SOS1, SOS2, Minimize, Maximize

DEFAULT_DOMAIN = Domain.real
DEFAULT_SOLVER_ORDER = ('cbc', 'gurobi', 'cbc')

class SymbolCatalog(object):
    __metaclass__ = Singleton

    def __init__(self):
        super(SymbolCatalog, self).__init__()
        self._names = set()
        self._symbols = {}
        self._options_funcs = {}

    _domain_mapping = {
        Domain.real: pyoenv.Reals,
        Domain.integer: pyoenv.Integers,
        Domain.binary: pyoenv.Binary,
        None: None
    }

    def _register_name(self, name):
        if name is not None:
            if name in self._names:
                raise ValueError('a symbol named {} already exists'.format(name))
            elif name == '':
                raise ValueError('empty string is not an allowed symbol name')
            elif not isinstance(name, str):
                raise ValueError('symbol name should be a string')
        self._names.add(name)

    def _make(self, options):
        name = options.pop('name')
        self._register_name(name)
        options['domain'] = self._domain_mapping[options.get('domain', None)]
        symbol = pyoenv.Var(**options)
        symbol.name = name
        return symbol

    def register(self, owner, options_func):
        self._options_funcs[owner] = options_func

    def get(self, owner, index):
        if not (owner, index) in self._symbols:
            self._symbols[owner, index] = self._make(self._options_funcs[owner](index))
        return self._symbols[owner, index]

    def set(self, owner, index, value):
        try:
            self._symbols[owner, index] = float(value)
        except TypeError:
            raise TypeError("Set variables to float-like things (you sent '{}').".format(value))

    def variables(self):
        return self._symbols.values()
    


class Variable(object):
    """docstring for Variable"""
    
    def __init__(self, name, lb=None, ub=None, domain=DEFAULT_DOMAIN):
        super(Variable, self).__init__()
        self._name = name
        self._lb = lb
        self._ub = ub
        self._domain = domain
        SymbolCatalog().register(self, self._symbol_options)

    @property
    def name(self):
        return self._name

    @property
    def domain(self):
        return self._domain
        
    @property
    def lb(self):
        return self._lb

    @property
    def ub(self):
        return self._ub


    def __call__(self, index=None):
        return SymbolCatalog().get(self, index)

    def _symbol_options(self, index):
        if index is None:
            name = self.name
        else:
            name = '{}[{}]'.format(self.name, index)

        lb = self._lb(index) if callable(self._lb) else self._lb
        ub = self._ub(index) if callable(self._ub) else self._ub

        return dict(name=name, bounds=(lb, ub), domain=self.domain)


    def replace_symbols(self, data, indices):
        for index, symbol in indices:
            if symbol in data:
                SymbolCatalog().set(self, index, data[symbol])


    def constraint_func(self, index):
        # Not used in this implementation, but in principle a Variable may produce constraints
        # which should be added to to any optimization problem where the variable is used.
        # This was used to produce upper and lower bounds in the previous implementation 
        # which used sympy symbols instead of Pyomo variables.
        #
        # It is still used in the subclass PiecewiseAffineArg, by the way.
        #
        # I'm leaving it in here in case someone, someday implements some other
        # optimization engine that needs this.
        return set()



class PiecewiseAffineArg(Variable):
    """docstring for Variable"""
    def __init__(self, name, points):
        super(PiecewiseAffineArg, self).__init__(name)
        self.points = points
        SymbolCatalog().register(self, self._symbol_options)

    def __call__(self, index=None):
        return self.weighted_sum(index)

    def weighted_sum(self, index):
        return sum([point * weight for point, weight in zip(self.points, self.weights(index))])

    def weights(self, index):
        cat = SymbolCatalog()
        return tuple(cat.get(self, (index, point)) for point in self.points)

    def _symbol_options(self, (index, point)):
        if index is None:
            name = '{}_{}'.format(self.name, point)
        else:
            name = '{}_{}[{}]'.format(self.name, point, index)

        return dict(name=name, bounds=(0, 1), domain=Domain.real)
    
    def replace_symbols(self, data, indices):
        for index, symbol in indices:
            for point in self.points:
                if symbol in data:
                    SymbolCatalog().set(self, (index, point), data[symbol])

    def constraint_func(self, index):
        weights = self.weights(index)
        constraints = (
            SOS2(weights, desc='Weights of points in piecewise affine expression'),
            Constraint(sum(weights) == 1, desc='Sum of weights in piecewise affine expression'))
        return constraints


class Problem(object):
    """An optimization problem"""
    def __init__(self):
        super(Problem, self).__init__()
        self.constraints = set()
        self.objective = None
        self._solver_order = DEFAULT_SOLVER_ORDER
        self._solver = None

    _solver_funcs = {
        'gurobi': lambda: SolverFactory('gurobi', solver_io='python'),
        'cbc': lambda: SolverFactory('cbc', solver_io='nl')
        }

    def use_solver(self, *order):
        self._solver_order = order

    def _get_solver(self):
        if len(self._solver_order) == 0:
            names = DEFAULT_SOLVER_ORDER
        else:
            names = self._solver_order

        for name in names:
            exceptions = []
            try:
                return self._solver_funcs[name]()
            except Exception, e:
                exceptions.append({'solver_name': name, 'exception': str(e)})

        raise RuntimeError('No solver could be initialized. More info: {}'.format(exceptions))

    def solve(self):
        """Try to solve the optimization problem"""

        if self._solver is None:
            self._solver = self._get_solver()
        
        model = pyoenv.ConcreteModel()

        for v in SymbolCatalog().variables():
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

        result = self._solver.solve(model)

        if not result.Solution.Status == pyomo.opt.SolutionStatus.optimal:
            raise SolverError("pyomo solution status is '{0}'".format(result.Solution.Status))

        model.load(result)


