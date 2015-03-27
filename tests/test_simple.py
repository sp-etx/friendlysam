from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import super
from future import standard_library
standard_library.install_aliases()

from itertools import chain
from friendlysam.model import Node, Storage, Cluster, ResourceNetwork
from friendlysam.optimization import *
from friendlysam.optimization.pyomoengine import PyomoSolver

RESOURCE = 0
ABSTOL = 1e-6

class Producer(Node):
    """docstring for Producer"""
    def __init__(self, param, **kwargs):
        super(Producer, self).__init__(**kwargs)

        self.activity = self.variable_collection('activity', lb=0)

        self.production[RESOURCE] = self.activity

        self.cost = lambda t: param(t) * self.activity(t)


class Consumer(Node):
    """docstring for Consumer"""
    def __init__(self, param, **kwargs):
        super(Consumer, self).__init__(**kwargs)
        
        self.activity = self.variable_collection('activity', lb=0)
        self.consumption[RESOURCE] = self.activity
        cons = self.consumption[RESOURCE]

        self += lambda t: (Constraint(cons(t) == param(t)),)


def approx(a, b):
    return abs(a-b) <= ABSTOL


def test_basic_functionality():
    times = range(1,4)

    consumption = lambda t: t * 1.5
    V0 = 10

    p = Producer(lambda t: t ** 2, name='Producer')
    c = Consumer(consumption, name='Consumer')
    s = Storage(RESOURCE, capacity=15, name='Storage')
    s.volume(0).value = V0
    rn = ResourceNetwork(RESOURCE)
    rn.connect(p, s)
    rn.connect(s, c)

    prob = Problem()
    prob.add_constraints(chain(*(rn.constraints(t) for t in times)))

    prob.objective = Minimize(sum(p.cost(t) for t in times))

    solution = PyomoSolver().solve(prob)

    for t in times:
        c.activity(t).take_value(solution)
        p.activity(t).take_value(solution)
        s.volume(t).take_value(solution)

    for t in times:
        assert approx(p.activity(t).value, 0)
        assert approx(c.activity(t).value, consumption(t))
        assert approx(s.volume(t).value, s.volume(t-1).value + s.accumulation[RESOURCE](t-1).evaluate({}))


if __name__ == '__main__':
    test_basic_functionality()