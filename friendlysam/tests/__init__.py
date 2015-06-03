# -*- coding: utf-8 -*-

from friendlysam import get_solver

default_solver = get_solver()

ABSTOL = 1e-6

def approx(a, b):
    return abs(a-b) <= ABSTOL