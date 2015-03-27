# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import super
from future import standard_library
standard_library.install_aliases()

from friendlysam.optimization.pyomoengine import PyomoSolver

default_solver = PyomoSolver()
default_solver.options['solver_order'] = [dict(name='cbc', solver_io='nl')]

ABSTOL = 1e-6

def approx(a, b):
    return abs(a-b) <= ABSTOL