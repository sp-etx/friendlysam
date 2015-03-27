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
from friendlysam.optimization import Problem, Minimize, SolverError
from friendlysam.tests import default_solver, approx
from friendlysam.tests.simple_models import Producer, Consumer, RESOURCE



def test_cluster():
    times = list(range(1,4))

    consumption = lambda t: t * 1.5

    p = Producer(name='Producer')
    c = Consumer(consumption, name='Consumer')
    cl = Cluster(p, c, resource=RESOURCE, name='Cluster')

    prob = Problem()
    prob.add_constraints(chain(*(cl.constraints(t) for t in times)))

    prob.objective = Minimize(sum(p.cost(t) for t in times))

    solution = default_solver.solve(prob)

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
def test_balance_simple():

    time = 0
    consumption = lambda t: 1
    c = Consumer(consumption, name='Consumer')

    prob = Problem()
    prob.add_constraints(c.constraints(time))

    prob.objective = Minimize(c.consumption[RESOURCE](time))

    # Raises SolverError because the consumer wants to consume but noone delivers
    solution = default_solver.solve(prob)
