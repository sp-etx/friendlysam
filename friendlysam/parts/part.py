# coding=utf-8

from __future__ import division

import sympy

class VariableError(Exception): pass

class Constrained(object):
    """docstring for Constrained"""
    def __init__(self):
        super(Constrained, self).__init__()
        self._constraint_funcs = set()
        self._var_counter = 0
        self._vars = {}

    def add_constraint(self, c):
        self._constraint_funcs.add(c)

    def constraints(self, *args, **kwargs):
        all_constraints = set()

        for func in self._constraint_funcs:
            constraints = func(*args, **kwargs)
            try: # iterable?
                all_constraints.update(constraints)
            except TypeError: # not iterable!
                all_constraints.add(constraints)

        return all_constraints

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
        self._opt_setup_funcs = list()

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


    def _augment_var_name(self, name):
        return '{}.{}'.format(self.name, name)

    def _register_var_name(self, name=None):
        if name:
            name = self._augment_var_name(name)
        if name in self._vars:
            raise VariableError('variable {} already exists'.format(name))
        while not name or name in self._vars:
            self._var_counter += 1
            name = self._augment_var_name('var{}'.format(self._var_counter))
        return name


    def make_var(self, name=None, lb=None, ub=None):
        name = self._register_var_name(name)
        symbol = sympy.Symbol(name)
        self._vars[name] = symbol

        if lb is not None:
            raise NotImplementedError() # should register constraints for lower bound

        if ub is not None:
            raise NotImplementedError() # should register constraints for upper bound

        return symbol