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
from friendlysam.optimization import Problem, Minimize, Constraint, SolverError, PiecewiseAffine
from friendlysam.tests import default_solver, approx
from friendlysam.compat import ignored


def test_basic():
    pwa = PiecewiseAffine((1, 1.5, 2), name='aoeu')
    prob = Problem()
    prob.constraints.update(pwa.constraints)
    prob.objective = Minimize(pwa.func([3, 2, 4]))

    solution = default_solver.solve(prob)
    for w in pwa.weights:
        w.take_value(solution)

    assert(approx(pwa.arg.value, 1.5))


if __name__ == '__main__':
    test_basic()