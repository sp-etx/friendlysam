# -*- coding: utf-8 -*-

from friendlysam.model import Node
from friendlysam.optimization import Constraint, namespace, VariableCollection

RESOURCE = 0

class Producer(Node):
    """docstring for Producer"""
    def __init__(self, **kwargs):
        super(Producer, self).__init__(**kwargs)

        with namespace(self):
            self.activity = VariableCollection('activity', lb=0)
        self.production[RESOURCE] = lambda t: 2 * self.activity(t)
        self.cost = lambda t: 3 * self.activity(t)


class Consumer(Node):
    """docstring for Consumer"""
    def __init__(self, consumption, **kwargs):
        super(Consumer, self).__init__(**kwargs)
        
        with namespace(self):
            self.activity = VariableCollection('activity', lb=0)
        self.consumption[RESOURCE] = lambda t: self.activity(t) * 0.5
        cons = self.consumption[RESOURCE]
        self.constraints += lambda t: Constraint(cons(t) == consumption(t), 'Consumption constraint')
