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
    prob.add(fs.SOS1(vs))
    prob.add(Constraint(fs.Eq(sum(vs), sum_val)))
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


def test_simple_pwa_1():
    x_vals = (1, 1.5, 2)
    y_vals = [3, 2, 4]
    x, y, constraints = fs.piecewise_affine(zip(x_vals, y_vals), name='aoeu')
    prob = fs.Problem()
    prob.objective = fs.Minimize(y)
    prob.add(constraints)

    solution = default_solver.solve(prob)
    print(solution)
    for var in x.variables:
        var.take_value(solution)

    assert(approx(x.value, 1.5))
    assert(approx(y.value, 2))

def test_simple_pwa_2():
    points = {1: 3, 1.5: 2, 2: 4}
    x, y, constraints = fs.piecewise_affine(points, name='aoeu')
    prob = fs.Problem()
    prob.objective = fs.Maximize(y)
    prob.add(constraints)

    solution = default_solver.solve(prob)
    print(solution)
    for var in x.variables:
        var.take_value(solution)

    assert(approx(x.value, 2))
    assert(approx(y.value, 4))


if __name__ == '__main__':
    test_simple_pwa_2()