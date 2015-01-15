# coding=utf-8

from __future__ import division

import friendlysam.optimization as opt
from friendlysam.optimization.pyomoengine import Variable

class Part(object):
    """docstring for Part"""

    _part_counter = 0

    def __init__(self, name=None):
        super(Part, self).__init__()
        self._constraint_funcs = set()
        self._model = None
        Part._part_counter += 1
        
        if name is None:
            name = 'Part' + str(Part._part_counter)
        self.name = name

        self._parts = set()

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

    def __iadd__(self, other):
        if callable(other):
            self._constraint_funcs.add(other)
        else:
            raise ValueError("'{}' cannot be added to '{}'".format(other, self))

        return self

    @property
    def engine(self):
        try:
            return self.model.engine
        except AttributeError:
            return None

    @property
    def model(self):
        return self._model
    @model.setter
    def model(self, value):
        self._model = value
        for p in self.parts(0):
            p.model = value
    

    def parts(self, depth='all'):
        parts = set()
        if depth is 'all' or depth >= 0:
            parts.update(self._parts)

        next_level = 'all' if depth is 'all' else (depth - 1)
        all_parts = parts.union(*(subpart.parts(next_level) for subpart in parts))

        return all_parts

    def add_part(self, p):
        if self in p.parts():
            raise ValueError('cannot add ' + str(p) + ' to ' + str(self) +
                ' because it would generate a cyclic relationship')

        self._parts.add(p)
        p.model = self.model


    def add_parts(self, *parts):
        for p in parts:
            self.add_part(p)


    def variable(self, name=None, **kwargs):
        name = '{}.{}'.format(self.name, name)
        variable = Variable(name=name, **kwargs)
        self._constraint_funcs.add(variable.constraint_func)
        variable.owner = self
        return variable


    def constraints(self, indices=(None,), depth='all'):
        constraints = set()
        for func in self._constraint_funcs:
            for index in indices:
                func_output = func(index)
                try:
                    constraints.update(func_output)
                except TypeError: # not iterable
                    raise opt.ConstraintError(
                        "the constraint function '{}' did not return an iterable".format(func))

        # Subtract 1 from depth. This means we get only this part's constraints
        # if depth=0, etc. It is probably the expected behavior.
        depth = depth if depth is 'all' else (depth - 1)
        subparts = self.parts(depth)
        return constraints.union(*(p.constraints(indices, depth=0) for p in subparts))




class Model(Part):
    """docstring for Model"""
    def __init__(self):
        super(Model, self).__init__()
        self._engine = None

    @property
    def engine(self):
        return self._engine
    @engine.setter
    def engine(self, value):
        self._engine = value

    @property
    def model(self):
        return self