import sympy

class Variable(object):
    """docstring for Variable"""
    def __init__(self, name, lb=None, ub=None, integer=False):
        super(Variable, self).__init__()
        self.name = name
        self.lb = lb
        self.ub = ub
        self.integer = integer
        self._symbols = {}

    def __call__(self, index=None):
        if not index in self._symbols:
            self._symbols[index] = self._make_symbol(index)
        return self._symbols[index]

    def replace_symbols(self, data, indices):
        for idx in indices:
            if idx in self._symbols:
                self._symbols[idx] = self.try_replace(self._symbols[idx], data)
            
    def _make_symbol(self, index):
        return sympy.Symbol('{}[{}]'.format(self.name, index))

    def constraint_func(self):
        return []

    def try_replace(self, something, data):
        return something.xreplace(data) if isinstance(something, sympy.Basic) else something


class PiecewiseAffineArg(Variable):
    """docstring for Variable"""
    def __init__(self, name, points):
        super(PiecewiseAffineArg, self).__init__(name)
        self.points = points

    def __call__(self, index=None):
        if not index in self._symbols:
            self._symbols[index] = self._make_symbols(index)
        return sum([point * weight for point, weight in zip(self.points, self._symbols[index])])

    def _make_symbols(self, index):
        return [sympy.Symbol('{}_{}[{}]'.format(self.name, i, index)) for i in self.points]

    def replace_symbols(self, data, indices):
        for idx in indices:
            if idx in self._symbols:
                self._symbols[idx] = [self.try_replace(s, data) for s in self._symbols[idx]]


class ProcessA(object):
    """docstring for ProcessA"""
    def __init__(self):
        super(ProcessA, self).__init__()
        self.variables = set()
        self._constraint_funcs = set()

        self += Variable('x', lb=0, integer=True)
        self += PiecewiseAffineArg('y', [0, .4, .6, 1])



    def __iadd__(self, other):
        if isinstance(other, Variable):
            variable = other
            local_name = variable.name
            if hasattr(self, local_name):
                raise AttributeError("an attribute named '{}' already exists".format(local_name))
            variable.name = 'foo.' + variable.name
            setattr(self, local_name, variable)
            self.variables.add(variable)

        return self

    def replace_symbols(self, data, indices=(None,)):
        for v in self.variables:
            v.replace_symbols(data, indices)




a = ProcessA()
print(a.x())
a.replace_symbols({a.x(): 30.5})
print(a.x())
a.replace_symbols({a.x(): 30.5})
print(a.y())


# c = CHP()

# cost = c.cost + ...
# #optimize a little

# c.replace_symbols(result)