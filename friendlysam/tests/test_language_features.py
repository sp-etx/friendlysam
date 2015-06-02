# -*- coding: utf-8 -*-

from nose.tools import raises, assert_raises

from itertools import chain, product
import friendlysam as fs
from friendlysam import Node, Cluster, Constraint, namespace

from friendlysam.tests import default_solver, approx
from friendlysam.tests.simple_models import Producer, RESOURCE
from friendlysam.compat import ignored

class Consumer(Node):
    """docstring for Consumer"""
    def __init__(self, consumption, variant, **kwargs):
        super(Consumer, self).__init__(**kwargs)
        
        self._cons_func = consumption
        with namespace(self):
            self.activity = fs.VariableCollection('activity', lb=0)
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


def check_variant(variant, sum_func=sum):
    times = list(range(5))
    consumption = lambda t: t * 1.5

    p = Producer(name='Producer')
    c = Consumer(consumption, variant)
    cl = Cluster(p, c, resource=RESOURCE, name='Cluster')

    prob = fs.Problem()
    prob += (part.constraints(t) for part, t in product(cl.descendants_and_self, times))

    prob.objective = fs.Minimize(sum_func(p.cost(t) for t in times))

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
    cl.constraints += fs.Variable() == 3

def test_variants():
    for variant in range(5):
        yield check_variant, variant
        yield check_variant, variant, fs.Sum


if __name__ == '__main__':
    non_callable_constraint()