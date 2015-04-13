# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import super
from future import standard_library
standard_library.install_aliases()

from friendlysam.optimization.pulpengine import PulpSolver

default_solver = PulpSolver()

ABSTOL = 1e-6

def approx(a, b):
    return abs(a-b) <= ABSTOL