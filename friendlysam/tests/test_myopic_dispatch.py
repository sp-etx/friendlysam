# -*- coding: utf-8 -*-

from nose.tools import raises, assert_raises

from itertools import chain, product

import friendlysam as fs
from friendlysam import Node, Cluster

from friendlysam.tests import default_solver, approx
from friendlysam.tests.simple_models import Producer, Consumer, RESOURCE



def test_state_vars():
    consumption = lambda t: t * 1.5

    p = Producer(name='Producer')
    c = Consumer(consumption, name='Consumer')
    cl = Cluster(p, c, resource=RESOURCE, name='Cluster')

    m = fs.models.MyopicDispatchModel(t0=0, step=3, horizon=7)
    m.add_part(cl)
    m.solver = default_solver
    m.advance()
    m.advance()

test_state_vars()