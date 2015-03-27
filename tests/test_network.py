from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import super
from future import standard_library
standard_library.install_aliases()

from nose.tools import raises, assert_raises

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


def test_cluster_balance_constraint():
    n = Node()
    n.production[RESOURCE] = lambda: 0
    assert len(n.constraints()) == 1
    c = Cluster(n, resource=RESOURCE)
    assert len(n.constraints()) == 0
    c.remove_part(n)
    assert len(n.constraints()) == 1


def test_cluster_add_remove():
    n = Node()
    n.production[RESOURCE] = lambda: 0
    c = Cluster(resource=RESOURCE)

    def not_added():
        return c.parts() == set() and n.cluster(RESOURCE) is None

    def added():
        return c.parts() == {n} and n.cluster(RESOURCE) is c

    assert not_added()
    c.add_part(n)
    assert added()
    c.add_part(n)

    c.remove_part(n)
    assert not_added()
    c.remove_part(n)
    
    n.set_cluster(c)
    assert added()
    assert_raises(InsanityError, n.set_cluster, c)

    n.unset_cluster(c)
    assert not_added()
    assert_raises(InsanityError, n.unset_cluster, c)


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
    test_cluster_add_remove()
