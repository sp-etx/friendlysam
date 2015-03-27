from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import super
from future import standard_library
standard_library.install_aliases()

from itertools import chain

from nose.tools import raises

from friendlysam.model import Storage, ResourceNetwork, InsanityError
from friendlysam.tests.simple_models import Producer, Consumer, RESOURCE
from friendlysam.tests import default_solver, approx
from friendlysam.optimization import Problem, Minimize

def test_basic_functionality():
    times = range(1,4)

    consumption = lambda t: t * 1.5
    V0 = 10

    p = Producer(name='Producer')
    c = Consumer(consumption, name='Consumer')
    s = Storage(RESOURCE, capacity=15, name='Storage')
    s.volume(0).value = V0
    rn = ResourceNetwork(RESOURCE)
    rn.connect(p, s)
    rn.connect(s, c)

    prob = Problem()
    prob.add_constraints(chain(*(rn.constraints(t) for t in times)))

    prob.objective = Minimize(sum(p.cost(t) for t in times))

    solution = default_solver.solve(prob)

    for t in times:
        c.activity(t).take_value(solution)
        p.activity(t).take_value(solution)
        s.volume(t).take_value(solution)

    for t in times:
        assert approx(p.activity(t).value, 0)
        assert approx(c.consumption[RESOURCE](t).value, consumption(t))
        assert approx(s.volume(t).value, s.volume(t-1).value + s.accumulation[RESOURCE](t-1).value)


@raises(InsanityError)
def test_not_indexed_w_storage():
    s = Storage(RESOURCE)
    s.constraints()
