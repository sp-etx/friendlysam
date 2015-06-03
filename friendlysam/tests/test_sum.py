# -*- coding: utf-8 -*-

from nose.tools import raises, assert_raises

import friendlysam as fs

def test_sum_syntax():
    empty = ()
    assert_raises(TypeError, fs.Sum) # Cannot create Sum()
    assert_raises(TypeError, fs.Sum, 1) # Cannot create Sum(1)
    assert_raises(TypeError, fs.Sum, 1, 2) # Cannot create Sum(1, 2)
    
    assert 0 == fs.Sum(empty) == fs.Sum([]) == fs.Sum(i for i in empty)

def test_sum_equality():
    a = fs.Sum(range(100))
    b = fs.Sum([i for i in range(100)])
    c = fs.Sum(tuple(range(100)))
    assert a == b == c
    
def test_nested_expressions():
    x = fs.Variable('x')
    y = fs.Variable('x')
    nested_expr_1 = fs.Sum([x, x * (x + 1), 2, x]) # Only x
    nested_expr_2 = fs.Sum([x, x * (y + 1), 2, y]) # A couple of x exchanged for y
    assert nested_expr_1 == nested_expr_2.evaluate(replace={y:x})
