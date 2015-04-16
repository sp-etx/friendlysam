# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

from itertools import chain, product
from collections import OrderedDict
from enum import Enum, unique

import friendlysam as fs


@unique
class Resources(Enum):
    natural_gas = 1
    power = 2
    heat = 3
    msw = 4
    biofuel = 5
    heating_oil = 6


class Boiler(fs.Node):
    """docstring for Boiler"""
    def __init__(self, fuel=None, eta=None, Fmax=None, fuel_cost=None, **kwargs):
        super().__init__(**kwargs)

        with fs.namespace(self):
            F = fs.VariableCollection(lb=0, ub=Fmax)
        self.consumption[fuel] = F
        self.production[Resources.heat] = lambda t: eta * F(t)

        self.cost = lambda t: fuel_cost * F(t)
        self.state_variables = lambda t: {F(t)}


class LinearCHP(fs.Node):
    """docstring for LinearCHP"""
    def __init__(self, fuel=None, alpha=None, eta=None, Fmax=None, fuel_cost=None, **kwargs):        
        super().__init__(**kwargs)

        with fs.namespace(self):
            F = fs.VariableCollection(lb=0, ub=Fmax)

        self.consumption[fuel] = F
        self.production[Resources.heat] = lambda t: F(t) * eta / (alpha + 1)
        self.production[Resources.power] = lambda t: alpha * self.production[Resources.heat](t)

        self.cost = lambda t: fuel_cost * F(t)
        self.state_variables = lambda t: {F(t)}


class LinearSlowCHP(fs.Node):
    """docstring for LinearSlowCHP"""
    def __init__(self, startup_time=None, fuel=None, alpha=None, eta=None, 
                 Fmin=None, Fmax=None, fuel_cost=None, **kwargs):
        super().__init__(**kwargs)


        mode_names = ('off', 'starting', 'on')
        with fs.namespace(self):
            modes = OrderedDict(
                (n, VariableCollection(name=n, domain=fs.Domain.binary)) for n in mode_names)
            F_on = fs.VariableCollection(lb=0) # Fuel use if on

        self.consumption[fuel] = lambda t: F_on(t) * modes['on'](t) + modes['starting'](t) * Fmin
        self.production[Resources.heat] = lambda t: modes['on'] * F_on(t) * eta / (alpha + 1)
        self.production[Resources.power] = lambda t: alpha * self.production[Resources.heat](t)

        on_or_starting = lambda t: modes['on'](t) + modes['starting'](t)
        def mode_constraints(t):
            yield Constraint(
                sum(m(t) for m in modes.values()) == 1, desc='Exactly one mode at a time')

            recent_sum = sum(on_or_starting(t-tau-1) for tau in range(starting_time))
            yield Constraint(
                modes['on'](t) <= recent_sum / startup_time,
                desc="'on' mode is only allowed after startup_time in 'on' and 'starting'")

            yield Constraint(
                self.consumption[fuel](t) <= Fmax * modes['on'] + Fmin * modes['starting'],
                desc='Max fuel use')

        self.constraints += mode_constraints

        self.cost = lambda t: fuel_cost * self.consumption[fuel](t)
        self.state_variables = lambda t: {F_on(t)} | {var(t) for var in self.modes.values()}



class Consumer(fs.Node):
    """docstring for Consumer"""
    def __init__(self, resource=None, consumption=None, **kwargs):
        super(Consumer, self).__init__(**kwargs)
        self.consumption[resource] = consumption

        self.cost = lambda t: 0
        self.state_variables = lambda t: tuple()


class HeatPump(fs.Node):
    """docstring for HeatPump"""
    def __init__(self, COP=None, Qmax=None, power_cost=None, **kwargs):
        super(HeatPump, self).__init__(**kwargs)

        with fs.namespace(self):
            Q = fs.VariableCollection(lb=0, ub=Qmax)
        self.production[Resources.heat] = Q
        self.consumption[Resources.power] = lambda t: Q / COP

        self.cost = lambda t: power_cost * self.consumption[Resources.power](t)
        self.state_variables = lambda t: {Q(t)}


class Trade(fs.Node):
    """docstring for Trade"""
    def __init__(self, resource=None, max_import=None, max_export=None, price=None, **kwargs):
        super(Trade, self).__init__(**kwargs)

        with fs.namespace(self):
            net_import = fs.VariableCollection(lb=-max_export, ub=max_import)
        self.production[resource] = net_import

        if hasattr(price, '__getitem__'):
            self.cost = lambda t: price[t] * net_import(t)
        else:
            self.cost = lambda t: price * net_import(t)

        self.state_variables = lambda t: {net_import(t)}
