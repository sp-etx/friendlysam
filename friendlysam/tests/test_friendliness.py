# -*- coding: utf-8 -*-

from nose.tools import raises, assert_raises

from itertools import chain
import friendlysam as fs
from friendlysam import Node, Cluster

from friendlysam.tests import default_solver, approx
from friendlysam.tests.simple_models import Producer, Consumer, RESOURCE


def test_novalue():
    x = fs.Variable()
    expr = x + x

    assert not hasattr(x, 'value')
    assert_raises(fs.NoValueError, lambda something: something.value, x)
    assert_raises(fs.NoValueError, lambda something: something.value, expr)
    assert_raises(fs.NoValueError, lambda something: float(something), x)
    assert_raises(fs.NoValueError, lambda something: float(something), expr)
    assert_raises(fs.NoValueError, lambda something: int(something), x)
    assert_raises(fs.NoValueError, lambda something: int(something), expr)

    x.value = 1.5

    assert x.value == 1.5
    assert float(x) == 1.5
    assert int(x) == 1

    assert expr.value == 3.
    assert float(expr) == 3.
    assert int(expr) == 3

def test_relation_truth():
    x = fs.Variable()

    # we don't want people accidentally checking e.g. "if x <= 0"

    def test_relation_truth(relation):
        if relation:
            pass
    
    assert_raises(TypeError, test_relation_truth, x < 0)
    assert_raises(TypeError, test_relation_truth, x <= 0)
    assert_raises(TypeError, test_relation_truth, x == 0)
    assert_raises(TypeError, test_relation_truth, x >= 0)
    assert_raises(TypeError, test_relation_truth, x > 0)
