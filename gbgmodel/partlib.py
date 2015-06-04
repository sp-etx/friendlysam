# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

from itertools import chain, product
from collections import OrderedDict
from enum import Enum, unique
import numbers

import friendlysam as fs
from friendlysam import Constraint, VariableCollection

@unique
class Resources(Enum):
    natural_gas = 1
    power = 2
    heat = 3
    heating_oil = 4
    bio_oil = 5
    wood_chips = 6
    wood_pellets = 7


class Boiler(fs.Node):
    """docstring for Boiler"""

    def __init__(self, fuel=None, taxation=None, Fmax=None, eta=None, **kwargs):
        super().__init__(**kwargs)

        with fs.namespace(self):
            F = VariableCollection(lb=0, ub=Fmax, name='F')
        self.consumption[fuel] = F
        self.production[Resources.heat] = lambda t: eta * F(t)

        fuel_cons_tax = taxation('consumption', fuel, chp=False)
        self.cost = lambda t: self.consumption[fuel](t) * fuel_cons_tax

        self.state_variables = lambda t: {F(t)}


def _CHP_cost_func(node, taxation, fuel):
    fuel_cons_tax = taxation('consumption', fuel, chp=True)
    power_prod_tax = taxation('production', Resources.power, fuel=fuel)
    return lambda t: (
        node.consumption[fuel](t) * fuel_cons_tax +
        node.production[Resources.power](t) * power_prod_tax)
        

class LinearCHP(fs.Node):
    """docstring for LinearCHP"""

    def __init__(self, fuel=None, alpha=None, eta=None, Fmax=None, taxation=None, **kwargs):        
        super().__init__(**kwargs)

        with fs.namespace(self):
            F = VariableCollection(lb=0, ub=Fmax, name='F')

        self.consumption[fuel] = F
        self.production[Resources.heat] = lambda t: F(t) * eta / (alpha + 1)
        self.production[Resources.power] = lambda t: alpha * self.production[Resources.heat](t)

        self.state_variables = lambda t: {F(t)}
        self.cost = _CHP_cost_func(self, taxation, fuel)


class LinearSlowCHP(fs.Node):
    """docstring for LinearSlowCHP"""

    def __init__(self, start_steps=None, fuel=None, alpha=None, eta=None, 
                 Fmin=None, Fmax=None, taxation=None, **kwargs):
        super().__init__(**kwargs)

        mode_names = ('off', 'starting', 'on')
        with fs.namespace(self):
            modes = OrderedDict(
                (n, VariableCollection(name=n, domain=fs.Domain.binary)) for n in mode_names)
            F_on = VariableCollection(lb=0, name='F_on') # Fuel use if on

        self.consumption[fuel] = lambda t: F_on(t) + modes['starting'](t) * Fmin
        self.production[Resources.heat] = lambda t: F_on(t) * eta / (alpha + 1)
        self.production[Resources.power] = lambda t: alpha * self.production[Resources.heat](t)

        self.cost = _CHP_cost_func(self, taxation, fuel)

        on_or_starting = lambda t: modes['on'](t) + modes['starting'](t)
        def mode_constraints(t):
            yield Constraint(
                fs.Eq(fs.Sum(m(t) for m in modes.values()), 1), desc='Exactly one mode at a time')

            if start_steps > 0:
                recent_sum = fs.Sum(on_or_starting(tau) for tau in self.iter_times(t, -(start_steps+1), 0))
                yield Constraint(
                    modes['on'](t) <= recent_sum / start_steps,
                    desc="'on' mode is only allowed after start_steps in 'on' and 'starting'")

            yield Constraint(
                self.consumption[fuel](t) <= Fmax * modes['on'](t) + Fmin * modes['starting'](t),
                desc='Max fuel use')

        self.constraints += mode_constraints

        self.state_variables = lambda t: {F_on(t)} | {var(t) for var in modes.values()}


class HeatPump(fs.Node):
    """docstring for HeatPump"""

    def __init__(self, COP=None, Qmax=None, taxation=None, **kwargs):
        super().__init__(**kwargs)

        with fs.namespace(self):
            Q = VariableCollection(lb=0, ub=Qmax, name='Q')
        self.production[Resources.heat] = Q
        self.consumption[Resources.power] = lambda t: Q(t) / COP

        power_cons_tax = taxation('consumption', Resources.power)
        self.cost = lambda t: self.consumption[Resources.power](t) * power_cons_tax

        self.state_variables = lambda t: {Q(t)}


class Import(fs.Node):
    """docstring for Import"""

    def __init__(self, resource=None, capacity=None, price=None, **kwargs):
        super().__init__(**kwargs)

        with fs.namespace(self):
            quantity = VariableCollection(lb=0, ub=capacity, name='import')

        self.production[resource] = quantity

        if isinstance(price, numbers.Real):
            self.cost = lambda t: price * quantity(t)
        else:
            self.cost = lambda t: price[t] * quantity(t)

        self.state_variables = lambda t: {quantity(t)}
