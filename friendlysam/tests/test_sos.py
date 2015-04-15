# -*- coding: utf-8 -*-

from nose.tools import raises, assert_raises

from itertools import chain
import friendlysam as fs
from friendlysam import Constraint

from friendlysam.tests import default_solver, approx
from friendlysam.compat import ignored


def test_simple_SOS1():
    n = 4
    index = 2
    sum_val = 3.
    vs = [fs.Variable(lb=-1, domain=fs.Domain.integer) for i in range(n)]
    #vs[0] = fs.Variable(lb=-1, domain=fs.Domain.integer)
    weights = [1 for i in range(n)]
    weights[index] = 0.5
    prob = fs.Problem()
    prob.add_constraint(fs.SOS1(vs))
    prob.add_constraint(Constraint(sum(vs) == sum_val))
    #prob.constraints.update(Constraint(v >= 0) for v in vs)
    prob.objective = fs.Minimize(sum(v * w for v, w in zip(vs, weights)))

    solution = default_solver.solve(prob)
    print(solution)
    for v in vs:
        v.take_value(solution)

    for i in range(n):
        if i == index:
            assert(approx(vs[i].value, sum_val))
        else:
            assert(approx(vs[i].value, 0))


def test_simple_pwa():
    pwa = fs.PiecewiseAffine((1, 1.5, 2), name='aoeu')
    prob = fs.Problem()
    prob.objective = fs.Minimize(pwa.func([3, 2, 4]))

    solution = default_solver.solve(prob)
    print(solution)
    for var in pwa.variables:
        var.take_value(solution)

    assert(approx(pwa.arg.value, 1.5))


if __name__ == '__main__':
    test_simple_pwa()