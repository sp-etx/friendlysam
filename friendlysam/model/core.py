# coding=utf-8

from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from builtins import super
from builtins import str
from future import standard_library
standard_library.install_aliases()

from collections import defaultdict

from friendlysam.log import get_logger
logger = get_logger(__name__)

import friendlysam.optimization as opt
from friendlysam.compat import ignored


class InsanityError(Exception): pass


class ConstraintCollection(object):
    """docstring for ConstraintCollection"""
    def __init__(self, owner):
        super().__init__()
        self._owner = owner
        self._constraint_funcs = set()

    def _prepare(self, constraint, origin_desc):
        if isinstance(constraint, opt.Relation):
            constraint = opt.Constraint(constraint)

        if not isinstance(constraint, opt.Constraint):
            raise ValueError('cannot handle constraint {}'.format(constraint))

        if constraint.origin is None:
            constraint.origin = '{}, {}'.format(self._owner, origin_desc)

        return constraint

    def _func_description(self, func, *indices):
        func_desc = func.__name__
        if len(indices) == 1:
            return '{}({})'.format(func_desc, indices[0])
        else:
            return '{}{}'.format(func_desc, indices)

    def __call__(self, *indices, **kwargs):
        depth = kwargs.get('depth', 'inf')

        constraints = set()

        for func in self._constraint_funcs:
            func_output = func(*indices)
            try:
                func_output = iter(func_output)
            except TypeError: # not iterable
                func_output = (func_output,)

            func_desc = self._func_description(func, *indices)
            constraints.update(self._prepare(item, func_desc) for item in func_output)

        # Subtract 1 from depth. This means we get only this part's constraints
        # if depth=0, etc. It is probably the expected behavior.
        depth = float(depth) - 1
        subparts = self._owner.parts(depth=depth)
        return constraints.union(*[p.constraints(*indices, depth=0) for p in subparts])

    def _add_constraint_func(self, func):
        if not callable(func):
            raise RuntimeError('constraint funcs must be callable but {} is not'.format(func))
        self._constraint_funcs.add(func)

    def add(self, addition):
        try:
            for func in addition:
                self._add_constraint_func(func)
        except TypeError:
            self._add_constraint_func(addition)

    def __iadd__(self, addition):
        self.add(addition)
        return self


class Part(object):
    """docstring for Part"""

    _subclass_counters = defaultdict(int)

    def __init__(self, name=None):
        self._constraints = ConstraintCollection(self)
        self._model = None
        self._subclass_counters[type(self)] += 1
        
        if name is None:
            name = '{}{:04d}'.format(type(self).__name__, self._subclass_counters[type(self)])
        self.name = name

        self._parts = set()

    @property
    def constraints(self):
        return self._constraints

    @constraints.setter
    def constraints(self, value):
        if value is not self._constraints:
            raise AttributeError('you are not allowed to change this one')


    def __str__(self):
        return self.name

    def __getitem__(self, name):
        matches = [part for part in self.parts() if part.name == name]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) == 0:
            raise KeyError("'{}' has no part '{}'".format(self, name))
        elif len(matches) > 1:
            raise KeyError(
                "'{}' has more than one part '{}'".format(self, name))


    def parts(self, depth='inf'):
        parts = set()
        depth = float(depth)
        if depth >= 0:
            parts.update(self._parts)

        all_parts = parts.union(*(subpart.parts(depth - 1) for subpart in parts))

        return all_parts

    def add_part(self, p):
        if self in p.parts('inf'):
            raise InsanityError(
                ('cannot add {} to {} because it would '
                'generate a cyclic relationship').format(p, self))

        self._parts.add(p)


    def remove_part(self, p):
        with ignored(KeyError):
            self._parts.remove(p)


    def add_parts(self, *parts):
        for p in parts:
            self.add_part(p)


    def variable(self, name=None, **kwargs):
        with opt.namespace(self):
            return opt.Variable(name=name, **kwargs)


    def variable_collection(self, name=None, **kwargs):
        with opt.namespace(self):
            return opt.VariableCollection(name=name, **kwargs)
