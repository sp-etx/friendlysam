# coding=utf-8

from __future__ import division

import friendlysam.optimization as opt

class Constrained(object):
    """docstring for Constrained"""
    def __init__(self):
        super(Constrained, self).__init__()
        self._fixed_constraints = set()
        self._indexed_constraints = set()

    def constrain(self, constraints):
        try:
            constraints = set(constraints)
        except TypeError: # not iterable
            constraints = set((constraints,))

        callables = set(filter(callable, constraints))
        other = constraints - callables

        self._indexed_constraints.update(callables)
        self._fixed_constraints.update(other)

    def constraints(self, indices=None):
        constraints = set()
        if indices:
            print('indices is', indices)
            print('_indexed_constraints', self._indexed_constraints)
            for func in self._indexed_constraints:
                for index in indices:
                    func_output = func(index)
                    try:
                        constraints.update(func_output)
                    except TypeError: # not iterable
                        constraints.add(func_output)

        constraints.update(self._fixed_constraints)

        return constraints


class Part(Constrained):
    """docstring for Part"""

    _part_counter = 0

    def __init__(self, name=None):
        super(Part, self).__init__()
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

    @property
    def parts(self):
        return self._parts

    def add_part(self, p):
        self._parts.add(p)
        
        if self in self.all_decendants:
            self._parts.remove(p)
            raise ValueError('cannot add ' + str(p) + ' to ' + str(self) +
                ' because it would generate a cyclic relationship')


    def add_parts(self, *parts):
        for p in parts:
            self.add_part(p)

    @property
    def all_decendants(self):
        return self.parts.union(
            *[p.all_decendants for p in self.parts])


    def register_var(self, name=None, indexed=False, **kwargs):
        var = opt.VariableFactory().make_var(name=name, indexed=indexed)
        if indexed:
            constraints = lambda idx: opt.make_constraints(var[idx], **kwargs)
        else:
            constraints = opt.make_constraints(var, **kwargs)
        self.constrain(constraints)
        return var