# coding=utf-8

from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from builtins import super
from builtins import str
from future import standard_library
standard_library.install_aliases()

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
        self._fixed_constraints = set()

    def _prepare(self, constraint, generic_description):
        if isinstance(constraint, opt.Relation):
            constraint = opt.Constraint(constraint)

        if not isinstance(constraint, opt.Constraint):
            raise ValueError('cannot handle constraint {}'.format(constraint))

        desc_start = '{}, {}'.format(self._owner, generic_description)
        if constraint.desc is None:
            constraint.desc = desc_start
        else:
            constraint.desc = '{}, {}'.format(desc_start, constraint.desc)

        return constraint

    def _func_description(self, func, *indices):
        func_desc = func.func_name
        if len(indices) == 1:
            return '{}({})'.format(func_desc, indices[0])
        else:
            return '{}{}'.format(func_desc, indices)

    def __call__(self, *indices, **kwargs):
        depth = kwargs.get('depth', 'inf')

        constraints = set()
        constraints.update(self._prepare(c, 'Fixed constraint') for c in self._fixed_constraints)

        for func in self._constraint_funcs:
            func_output = func(*indices)
            try:
                func_output = iter(func_output)
            except TypeError: # not iterable
                func_output = (func_output,)

            desc = self._func_description(func, *indices)
            constraints.update(self._prepare(item, desc) for item in func_output)

        # Subtract 1 from depth. This means we get only this part's constraints
        # if depth=0, etc. It is probably the expected behavior.
        depth = float(depth) - 1
        subparts = self._owner.parts(depth=depth)
        return constraints.union(*[p.constraints(*indices, depth=0) for p in subparts])

    def _add_one(self, constraint):
        destination = self._constraint_funcs if callable(constraint) else self._fixed_constraints
        destination.add(constraint)

    def __iadd__(self, addition):
        try:
            iterator = iter(addition)
        except TypeError:
            self._add_one(addition)
        else:
            for item in iterator:
                self._add_one(item)
        return self

    def add(self, addition):
        self.__iadd__(addition)


class Part(object):
    """docstring for Part"""

    _part_counter = 0

    def __init__(self, name=None):
        self._constraints = ConstraintCollection(self)
        self._model = None
        Part._part_counter += 1
        
        if name is None:
            name = 'Part' + str(Part._part_counter)
        self.name = name

        self._parts = set()

    @property
    def constraints(self):
        return self._constraints

    @constraints.setter
    def constraints(self, value):
        if value is not self._constraints:
            raise ValueError('you are not allowed to change this one')


    def __str__(self):
        return self.name

    def __getitem__(self, name):
        matches = [part for part in self.parts() if part.name == name]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) == 0:
            raise ValueError(
                "'" + str(self) + "' has no part '" + name + "'")
        elif len(matches) > 1:
            raise ValueError(
                "'" + str(self) + "' has more than one part '" + name + "'")


    def parts(self, depth='inf'):
        parts = set()
        depth = float(depth)
        if depth >= 0:
            parts.update(self._parts)

        all_parts = parts.union(*(subpart.parts(depth - 1) for subpart in parts))

        return all_parts

    def add_part(self, p):
        if self in p.parts('inf'):
            raise ValueError('cannot add ' + str(p) + ' to ' + str(self) +
                ' because it would generate a cyclic relationship')

        self._parts.add(p)


    def remove_part(self, p):
        with ignored(KeyError):
            self._parts.remove(p)


    def add_parts(self, *parts):
        for p in parts:
            self.add_part(p)


    def variable(self, name=None, **kwargs):
        name = '{}.{}'.format(self.name, name)
        variable = opt.Variable(name=name, **kwargs)
        return variable


    def variable_collection(self, name=None, **kwargs):
        name = '{}.{}'.format(self.name, name)
        collection = opt.VariableCollection(name=name, **kwargs)
        return collection
