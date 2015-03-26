from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import super
from future import standard_library
standard_library.install_aliases()

from nose.tools import raises

from itertools import chain
from friendlysam.model import Node, Storage, Cluster, ResourceNetwork, InsanityError
from friendlysam.optimization import *
from friendlysam.optimization.pyomoengine import PyomoSolver

RESOURCE = 0
ABSTOL = 1e-6

class Producer(Node):
    """docstring for Producer"""
    def __init__(self, param, **kwargs):
        super(Producer, self).__init__(**kwargs)

        self.activity = self.variable_collection('activity', lb=0)

        self.production[RESOURCE] = lambda t: self.activity(t) * 2

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


def test_cluster():
    times = range(1,4)

    consumption = lambda t: t * 1.5

    p = Producer(lambda t: t ** 2, name='Producer')
    c = Consumer(consumption, name='Consumer')
    cl = Cluster(p, c, resource=RESOURCE, name='Cluster')

    prob = Problem()
    prob.add_constraints(chain(*(cl.constraints(t) for t in times)))

    prob.objective = Minimize(sum(p.cost(t) for t in times))

    solution = PyomoSolver().solve(prob)

    for t in times:
        c.activity(t).take_value(solution)
        p.activity(t).take_value(solution)

    for t in times:
        assert approx(p.production[RESOURCE](t).evaluate({}), consumption(t))
        assert approx(c.consumption[RESOURCE](t).evaluate({}), consumption(t))


@raises(InsanityError)
def test_cluster_insanity():
    n = Node()
    Cluster(n, resource=RESOURCE)
    Cluster(n, resource=RESOURCE)


@raises(SolverError)
def test_balance():
    times = range(1,4)

    consumption = lambda t: t * 1.5

    c = Consumer(consumption, name='Consumer')

    prob = Problem()
    prob.add_constraints(chain(*(c.constraints(t) for t in times)))

    prob.objective = Minimize(sum(c.consumption[RESOURCE](t) for t in times))

    solution = PyomoSolver().solve(prob)


if __name__ == '__main__':
    test_cluster_insanity()
