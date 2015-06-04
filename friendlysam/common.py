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

def get_list(func, indices):
    return [float(func(index)) for index in indices]

def get_series(func, indices, **kwargs):
    if not pandas:
        raise RuntimeError('pandas is needed for this function').with_traceback(sys.exc_info()[2])
    return pandas.Series(index=indices, data=get_list(func, indices), **kwargs)