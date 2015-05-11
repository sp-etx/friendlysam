# -*- coding: utf-8 -*-

from nose.tools import raises, assert_raises

from itertools import chain, product

import friendlysam as fs
from friendlysam import Node, Cluster

from friendlysam.tests import default_solver, approx
from friendlysam.tests.simple_models import Producer, Consumer, RESOURCE



def test_state_vars():
    times = list(range(1,4))

    consumption = lambda t: t * 1.5

    p = Producer(name='Producer')
    c = Consumer(consumption, name='Consumer')
    cl = Cluster(p, c, resource=RESOURCE, name='Cluster')

    prob = fs.Problem()
    prob.add(chain(*(cl.constraints(t) for t in times)))

    prob.objective = fs.Minimize(sum(p.cost(t) for t in times))

    solution = default_solver.solve(prob)

    for t, part in product(times, cl.parts()):
        for v in part.state_variables(t):
            v.take_value(solution)

    for t in times:
        assert approx(p.production[RESOURCE](t).value, consumption(t))
        assert approx(c.consumption[RESOURCE](t).value, consumption(t))

