# coding=utf-8

from __future__ import division

class Part(object):
    """docstring for Part"""

    _element_counter = 0

    def __init__(self, name=None):
        super(Part, self).__init__()
        Part._element_counter += 1
        
        if name is None:
            name = 'Part' + str(Part._element_counter)
        self.name = name

        self._elements = set()
        self._opt_setup_funcs = list()

    def __str__(self):
        return self.name

    def __getitem__(self, name):
        matches = [e for e in self.all_decendants if e.name == name]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) == 0:
            raise ValueError(
                "'" + str(self) + "' has no element '" + name + "'")
        elif len(matches) > 1:
            raise ValueError(
                "'" + str(self) + "' has more than one element '" + name + "'")

    @property
    def elements(self):
        return self._elements

    def add_element(self, e):
        self._elements.add(e)
        
        if self in self.all_decendants:
            self._elements.remove(e)
            raise ValueError('cannot add ' + str(e) + ' to ' + str(self) +
                ' because it would generate a cyclic relationship')


    def add_elements(self, *elements):
        for e in elements:
            self.add_element(e)

    @property
    def all_decendants(self):
        return self.elements.union(
            *[e.all_decendants for e in self.elements])

    @property
    def all_elements(self):
        elements = self.all_decendants
        elements.add(self)
        return elements

    def _add_opt_setup(self, func):
        if not func in self._opt_setup_funcs:
            self._opt_setup_funcs.append(func)

    def _remove_opt_setup(self, func):
        self._opt_setup_funcs.remove(func)

    def setup_optimization_recursively(self, opt):
        for e in self.elements:
            e.setup_optimization_recursively(opt)

        if self in opt.elements:
            return

        for func in self._opt_setup_funcs:
            func(opt)

        opt.elements.add(self)

    def save_in(self, group):
        raise NotImplementedError()

    @staticmethod
    def load_from(group):
        raise NotImplementedError()

    def get_cost_expr(self, opt, t):
        return 0