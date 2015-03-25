# coding=utf-8

from __future__ import division

import friendlysam.optimization as opt

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


    def parts(self, depth):
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


    def constraints(self, depth, *indices):
        constraints = set()
        def add(func_output):
            try:
                constraints.update(func_output)
            except TypeError: # not iterable
                constraints.add(func_output)

        for func in self._constraint_funcs:
            if len(indices) == 0:
                add(func())
            else:
                for index in indices:
                    add(func(index))

        # Subtract 1 from depth. This means we get only this part's constraints
        # if depth=0, etc. It is probably the expected behavior.
        depth = float(depth) - 1
        subparts = self.parts(depth)
        return constraints.union(*[p.constraints(0, *indices) for p in subparts])

