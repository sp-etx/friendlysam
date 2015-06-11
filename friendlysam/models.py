# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

from itertools import chain, product

import friendlysam as fs
from friendlysam.compat import ignored

class MyopicDispatchModel(fs.Part):
    """docstring for MyopicDispatchModel"""
    def __init__(self, t0=None, horizon=None, step=None, name=None, require_cost=True):
        super().__init__(name=name)
        self.horizon = horizon
        self.step = step
        self.time = t0
        self.require_cost = require_cost
    
    def state_variables(self, t):
        return tuple()

    def cost(self, t):
        return 0

    def advance(self):
        if self.horizon < self.step:
            msg = '{}: horizon {} is smaller than step size {}'.format(
                repr(self),
                self.horizon,
                self.step)
            raise fs.InsanityError()

        opt_times = self.times(self.time, self.horizon)

        parts = self.descendants_and_self

        if self.require_cost is True:
            cost_contributors = parts
        else:
            cost_contributors = filter(self.require_cost, parts)
        system_cost = fs.Sum(p.cost(t) for p, t in product(cost_contributors, opt_times))

        problem = fs.Problem()
        problem.objective = fs.Minimize(system_cost)
        problem += (p.constraints.make(t) for p, t in product(parts, opt_times))

        solution = self.solver.solve(problem)

        for p, t in product(parts, self.iter_times(self.time, self.step)):
            for v in p.state_variables(t):
                v.take_value(solution)

        self.time = self.step_time(self.time, self.step)
