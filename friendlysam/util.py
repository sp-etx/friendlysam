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
    """Get a list of function values at indices.

    Args:
        func (callable): The callable to get values from.
        indices (iterable): An iterable of index values to pass to ``func``.

    Returns:
        list: values as ``float``

    Examples:

        >>> from friendlysam import Storage
        >>> s = Storage('power', name='Battery')
        >>> for i in range(5):
        ...     s.volume(i).value = i ** 2
        ...
        >>> get_list(s.accumulation['power'], range(4))
        [1.0, 3.0, 5.0, 7.0]
    """

    return [float(func(index)) for index in indices]

def get_series(func, indices, **kwargs):
    """Get a pandas Series of function values at indices.

    Equivalent to
    ``pandas.Series(index=indices, data=get_list(func, indices), **kwargs)``.

    Args:
        func (callable): The callable to get values from.
        indices (iterable): An iterable of index values to pass to ``func``.

    Returns:
        pandas.Series: Values at indices.

    Examples:

        >>> from friendlysam import Storage
        >>> s = Storage('power', name='Battery')
        >>> for i in range(5):
        ...     s.volume(i).value = i ** 2
        ...
        >>> get_series(s.accumulation['power'], range(4))
        0    1
        1    3
        2    5
        3    7
        dtype: float64
    """
    if not pandas:
        raise RuntimeError('pandas is needed for this function').with_traceback(sys.exc_info()[2])
    return pandas.Series(index=indices, data=get_list(func, indices), **kwargs)