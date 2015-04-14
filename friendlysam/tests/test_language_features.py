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
from friendlysam.optimization import Problem, Minimize, SolverError, Constraint, Variable, VariableCollection, namespace
from friendlysam.tests import default_solver, approx
from friendlysam.tests.simple_models import Producer, RESOURCE
from friendlysam.compat import ignored

class Consumer(Node):
    """docstring for Consumer"""
    def __init__(self, consumption, variant, **kwargs):
        super(Consumer, self).__init__(**kwargs)
        
        self._cons_func = consumption
        with namespace(self):
            self.activity = VariableCollection('activity', lb=0)
        self.consumption[RESOURCE] = lambda t: self.activity(t) * 0.5
        cons = self.consumption[RESOURCE]
        if variant == 0:
            self.constraints += lambda t: cons(t) == consumption(t)
        elif variant == 1:
            self.constraints += lambda t: (cons(t) == consumption(t), cons(t) == cons(t))
        elif variant == 2:
            self.constraints += (lambda t: cons(t) == consumption(t) for i in range(1))
        elif variant == 3:
            self.constraints += self._consumption_constraint
        elif variant == 4:
            self.constraints += lambda t: Constraint(cons(t) == consumption(t), 'Consumption')
        else:
            raise ValueError('variant {} not defined'.format(variant))

    def _consumption_constraint(self, t):
        return self.consumption[RESOURCE](t) == self._cons_func(t)


def check_variant(variant):
    times = list(range(5))
    consumption = lambda t: t * 1.5

    p = Producer(name='Producer')
    c = Consumer(consumption, variant)
    cl = Cluster(p, c, resource=RESOURCE, name='Cluster')

    prob = Problem()
    prob.add_constraints(chain(*(cl.constraints(t) for t in times)))

    prob.objective = Minimize(sum(p.cost(t) for t in times))

    solution = default_solver.solve(prob)

    for t in times:
        c.activity(t).take_value(solution)
        p.activity(t).take_value(solution)

    for t in times:
        assert approx(p.production[RESOURCE](t).value, consumption(t))
        assert approx(c.consumption[RESOURCE](t).value, consumption(t))


@raises(RuntimeError)
def non_callable_constraint():
    cl = Cluster(resource=RESOURCE)
    cl.constraints += Variable() == 3

def test_variants():
    for variant in range(5):
        yield check_variant, variant


if __name__ == '__main__':
    non_callable_constraint()