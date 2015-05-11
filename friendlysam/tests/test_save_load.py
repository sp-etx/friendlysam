# -*- coding: utf-8 -*-

import os

from nose.tools import raises, assert_raises

import dill
from itertools import chain
import friendlysam as fs

from friendlysam.tests import default_solver, approx
from friendlysam.tests.simple_models import Producer, Consumer, RESOURCE



def run_model(p, c, cl, times):
    times = tuple(times)

    prob = fs.Problem()
    prob.add(chain(*(cl.constraints(t) for t in times)))

    prob.objective = fs.Minimize(sum(p.cost(t) for t in times))

    solution = default_solver.solve(prob)

    for t in times:
        c.activity(t).take_value(solution)
        p.activity(t).take_value(solution)

    
FILENAME = 'test_save_load.pkl'
TIMES_1 = [1, 2, 3, 4]
TIMES_2 = [5, 6, 7, 8]

consumption = lambda t: t * 1.5

def run_and_save():

    p = Producer(name='Producer')
    c = Consumer(consumption, name='Consumer')
    cl = fs.Cluster(p, c, resource=RESOURCE, name='Cluster')

    run_model(p, c, cl, TIMES_1)

    with open(FILENAME, 'wb') as f:
        dill.dump((p, c, cl), f)


def test_load_and_run():
    run_and_save()
    with open(FILENAME, 'rb') as f:
        p, c, cl = dill.load(f)

    os.remove(FILENAME)

    run_model(p, c, cl, TIMES_2)
    for t in TIMES_1 + TIMES_2:
        assert approx(p.production[RESOURCE](t).value, consumption(t))
        assert approx(c.consumption[RESOURCE](t).value, consumption(t))
