# coding=utf-8

from __future__ import division

import friendlysam.optimization as opt
from friendlysam.optimization.pyomoengine import Variable

class Part(object):
    """docstring for Part"""

    _part_counter = 0

    def __init__(self, name=None):
        super(Part, self).__init__()
        self.constraint_funcs = set()
        self._model = None
        Part._part_counter += 1
        
        if name is None:
            name = 'Part' + str(Part._part_counter)
        self.name = name

        self._parts = set()

    def __str__(self):
        return self.name

    def __getitem__(self, name):
        matches = [part for part in self.all_decendants if part.name == name]
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
            self.constraint_funcs.add(other)
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
        for p in self.parts:
            p.model = value
    
    @property
    def parts(self):
        return self._parts

    def add_part(self, p):
        self._parts.add(p)
        
        if self in self.all_decendants:
            self._parts.remove(p)
            raise ValueError('cannot add ' + str(p) + ' to ' + str(self) +
                ' because it would generate a cyclic relationship')

        p.model = self.model


    def add_parts(self, *parts):
        for p in parts:
            self.add_part(p)

    @property
    def all_decendants(self):
        return self.parts.union(
            *[p.all_decendants for p in self.parts])


    def variable(self, name=None, **kwargs):
        name = '{}.{}'.format(self.name, name)
        variable = Variable(name=name, **kwargs)
        self.constraint_funcs.add(variable.constraint_func)
        variable.owner = self
        return variable


    def constraints(self, indices=(None,)):
        constraints = set()
        for func in self.constraint_funcs:
            for index in indices:
                func_output = func(index)
                try:
                    constraints.update(func_output)
                except TypeError: # not iterable
                    raise opt.ConstraintError(
                        "the constraint function '{}' did not return an iterable".format(func))

        return constraints




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