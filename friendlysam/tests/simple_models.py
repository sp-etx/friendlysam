# -*- coding: utf-8 -*-

import friendlysam as fs
from friendlysam import Constraint, namespace, VariableCollection

RESOURCE = 0

class Producer(fs.Node):
    """docstring for Producer"""
    def __init__(self, **kwargs):
        super(Producer, self).__init__(**kwargs)

        with namespace(self):
            self.activity = VariableCollection('activity', lb=0)
        self.production[RESOURCE] = lambda t: 2 * self.activity(t)
        self.cost = lambda t: 3 * self.activity(t)

    def state_variables(self, t):
        yield self.activity(t)


class Consumer(fs.Node):
    """docstring for Consumer"""
    def __init__(self, consumption, **kwargs):
        super(Consumer, self).__init__(**kwargs)
        
        with namespace(self):
            self.activity = VariableCollection('activity', lb=0)
        self.consumption[RESOURCE] = lambda t: self.activity(t) * 0.5
        cons = self.consumption[RESOURCE]
        self.constraints += lambda t: Constraint(fs.Equals(cons(t), consumption(t)), 'Consumption constraint')

    def state_variables(self, t):
        return [self.activity(t)]

    def cost(self, t):
        return 0
