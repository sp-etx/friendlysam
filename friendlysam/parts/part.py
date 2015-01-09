# coding=utf-8

from __future__ import division

import friendlysam.optimization as opt

class Constrained(object):
    """docstring for Constrained"""
    def __init__(self):
        super(Constrained, self).__init__()
        self.constraint_funcs = set()
        self.variables = set()

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


    def __iadd__(self, other):
        if isinstance(other, opt.Variable):
            variable = other
            local_name = variable.name
            if hasattr(self, local_name):
                raise AttributeError("an attribute named '{}' already exists".format(local_name))
            variable.name = '{}.{}'.format(self.name, variable.name)
            self.constraint_funcs.add(variable.constraint_func)
            setattr(self, local_name, variable)
            self.variables.add(variable)

        return self

    def replace_symbols(self, data, indices=(None,)):
        for v in self.variables:
            v.replace_symbols(data, indices)


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


    def variable(self, name=None, indexed=False, **kwargs):
        symbol = opt.SymbolFactory().symbol(name=name)
        constraints = opt.make_constraints(symbol, **kwargs)
        self.constrain(constraints)
        return symbol

    def variable_collection(self, name=None, **kwargs):
        collection = opt.SymbolFactory().symbol_collection(name=name)
        constraints = lambda idx: opt.make_constraints(collection[idx], **kwargs)
        self.constrain(constraints)
        return collection