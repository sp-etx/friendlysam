# -*- coding: utf-8 -*-

from nose.tools import raises, assert_raises

from itertools import chain, product

import friendlysam as fs
from friendlysam import Node, Cluster

from friendlysam.tests import default_solver, approx
from friendlysam.tests.simple_models import Producer, Consumer, RESOURCE



def test_series_simple():
    consumption = lambda t: t * 1.5

    p = Producer(name='Producer')
    c = Consumer(consumption, name='Consumer')
    cl = Cluster(p, c, resource=RESOURCE, name='Cluster')

    t0 = 0
    step = 3
    m = fs.models.MyopicDispatchModel(t0=t0, step=step, horizon=7)
    m.require_cost = lambda part: part is not cl
    m.add_part(cl)
    m.solver = default_solver
    m.advance()
    m.advance()

    times = m.times(t0, step * 2)
    prod = fs.get_series(p.production[RESOURCE], times)
    cons = fs.get_series(c.consumption[RESOURCE], times)
    for t in times:
        assert prod[t] == float(p.production[RESOURCE](t))
        assert cons[t] == float(c.consumption[RESOURCE](t))
        assert approx(prod[t], cons[t])
        assert ((prod-cons).abs() <= 1e-6).all()

