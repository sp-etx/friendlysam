# -*- coding: utf-8 -*-

import sys
import logging
logger = logging.getLogger(__name__)

import friendlysam as fs
from friendlysam.compat import ignored

try:
    import pandas
except ImportError:
    pandas = None

def _short_default_repr(obj, desc=None):
    if desc is None:
        return '<{}.{} at {}>'.format(obj.__module__, obj.__class__.__name__, hex(id(obj)))
    return '<{}.{} at {}: {}>'.format(obj.__module__, obj.__class__.__name__, hex(id(obj)), desc)

def get_list(func, indices):
    return [float(func(index)) for index in indices]

def get_series(func, indices, **kwargs):
    if not pandas:
        raise RuntimeError('pandas is needed for this function').with_traceback(sys.exc_info()[2])
    return pandas.Series(index=indices, data=get_list(func, indices), **kwargs)