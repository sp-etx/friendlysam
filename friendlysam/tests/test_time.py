# -*- coding: utf-8 -*-

from nose.tools import raises, assert_raises

import friendlysam as fs
import pandas as pd


def test_integer_time():
    part = fs.Part()
    t0 = 123145
    time_unit = 3

    assert part.step_time(t0, 42) == t0 + 42
    assert part.step_time(t0, -42) == t0 - 42

    part.time_unit = time_unit
    assert part.step_time(t0, 42) == t0 + 42 * time_unit
    assert part.step_time(t0, -42) == t0 - 42 * time_unit

    assert (
        (t0, t0+time_unit, t0+2*time_unit) ==
        part.times(t0, 3) ==
        tuple(part.iter_times(t0, 3)))

    assert () == part.times(t0, 0) == part.times(t0, -42) # Like range with negative argument
    assert (
        (t0 - 2*time_unit, t0 - time_unit, t0) ==
        part.times(t0, -2, 1) ==
        tuple(part.iter_times(t0, -2, 1))) # Just like tuple(range(-2, 1)) == (-2, -1, 0)

    assert part.times_between(t0-time_unit, t0+time_unit) == (t0-time_unit, t0, t0+time_unit)


def test_pandas_time():
    part = fs.Part()
    t0 = pd.Timestamp('2010')
    time_unit = pd.Timedelta('7h')
    almost_one_time_unit = pd.Timedelta('6h')

    part.time_unit = time_unit
    assert part.step_time(t0, 42) == t0 + 42 * time_unit
    assert part.step_time(t0, -42) == t0 - 42 * time_unit

    assert (
        (t0, t0+time_unit, t0+2*time_unit) ==
        part.times(t0, 3) ==
        tuple(part.iter_times(t0, 3)))

    assert () == part.times(t0, 0) == part.times(t0, -42) # Like range with negative argument
    assert (
        (t0 - 2*time_unit, t0 - time_unit, t0) ==
        part.times(t0, -2, 1) ==
        tuple(part.iter_times(t0, -2, 1))) # Just like tuple(range(-2, 1)) == (-2, -1, 0)

    assert part.times_between(t0-time_unit, t0+time_unit) == (t0-time_unit, t0, t0+time_unit)
    
    # times_between works with arbitrary end times
    assert len(part.times_between(t0, t0+almost_one_time_unit)) == 1
    assert (
        part.times_between(t0, t0+2*time_unit) == 
        part.times_between(t0, t0+2*time_unit+almost_one_time_unit))
