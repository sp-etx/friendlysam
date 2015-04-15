# -*- coding: utf-8 -*-

from friendlysam.solvers.pulpengine import PulpSolver

default_solver = PulpSolver()

ABSTOL = 1e-6

def approx(a, b):
    return abs(a-b) <= ABSTOL