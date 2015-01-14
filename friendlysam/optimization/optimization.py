# -*- coding: utf-8 -*-

from friendlysam.log import get_logger
logger = get_logger(__name__)

import itertools

from enum import Enum

class Domain(Enum):
    """docstring for Domain"""
    real = 0
    integer = 1
    binary = 2


class ConstraintError(Exception): pass


class _ConstraintBase(object):
    """docstring for _ConstraintBase"""
    def __init__(self, desc=None):
        super(_ConstraintBase, self).__init__()
        self.desc = desc

    def _add_desc(self, s):
        if self.desc is None:
            return s
        else:
            return '{} ({})'.format(s, self.desc)
        

class Constraint(_ConstraintBase):
    """docstring for Constraint"""
    def __init__(self, expr, desc=None):
        super(Constraint, self).__init__(desc)
        self.expr = expr

    def __str__(self):
        return self._add_desc(str(self.expr))


class _SOS(_ConstraintBase):
    """docstring for _SOS"""
    def __init__(self, sostype, symbols, desc=None):
        super(_SOS, self).__init__(desc)
        if not (isinstance(symbols, tuple) or isinstance(symbols, list)):
            raise ConstraintError('symbols must be a tuple or list')
        self._symbols = tuple(symbols)
        self._sostype = sostype

    def __str__(self):
        return self._add_desc('SOS{}{}'.format(self._sostype, self._symbols))

    @property
    def symbols(self):
        return self._symbols


class SOS1(_SOS):
    """docstring for SOS1"""
    def __init__(self, symbols, desc=None):
        super(SOS1, self).__init__(1, symbols, desc=desc)


class SOS2(_SOS):
    """docstring for SOS2"""
    def __init__(self, symbols, desc=None):
        super(SOS2, self).__init__(2, symbols, desc=desc)


class _Objective(object):
    """docstring for _Objective"""
    def __init__(self, expr):
        super(_Objective, self).__init__()
        self.expr = expr

class Maximize(_Objective):
    """docstring for Maximize"""
    pass

class Minimize(_Objective):
    """docstring for Minimize"""
    pass
