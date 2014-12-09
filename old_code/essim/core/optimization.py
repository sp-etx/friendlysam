# coding=utf-8

from __future__ import division

import gurobipy as gur

import pandas as pd

class OptimizationProblem(object):
    """docstring for OptimizationProblem"""
    def __init__(self, t0, timespan):
        super(OptimizationProblem, self).__init__()
        self.t0 = t0
        self.timespan = timespan

        self.elements = set()
        self.vars = dict()
        self._var_counter = 1
        self._constr_counter = 1
        self._prob = gur.Model('problem')
        self._prob.setParam('OutputFlag', False)
        self._solved = False
        self._dirty = False

    @property
    def times(self):
     return xrange(self.t0, self.t0 + self.timespan)

    def _update(self):
        if self._dirty:
            self._prob.update()
            self._dirty = False

    def _get_next_varname(self):
        name = 'x' + str(self._var_counter)
        self._var_counter += 1
        return name

    def _get_next_constrname(self):
        name = 'c' + str(self._constr_counter)
        self._constr_counter += 1
        return name

    def create_var(self, lb=0., ub=None, vtype='continuous', name=None):
        if vtype == 'continuous':
            gur_vtype = gur.GRB.CONTINUOUS
        elif vtype == 'binary':
            gur_vtype = gur.GRB.BINARY

        if lb is None:
            lb = -1.e21 # Treated as negative infinity by Gurobi

        if ub is None:
            ub = gur.GRB.INFINITY

        if name is not None:
            name = name.encode('ascii', 'replace')
            name += ' (' + self._get_next_varname() + ')'
        else:
            name = self._get_next_varname()

        var = self._prob.addVar(
            lb=lb, ub=ub, vtype=gur_vtype, name=name)
        self._dirty = True
        return var

    def add_constraint(self, c):
        if c == False or c == True:
            return
        self._update()
        self._prob.addConstr(c, self._get_next_constrname())

    def add_range(self, expr, lb, ub):
        self._update()
        self._prob.addRange(expr, lb, ub, name=self._get_next_constrname())

    def add_sos1_constraint(self, variables):
        self._update()
        self._prob.addSOS(gur.GRB.SOS_TYPE1, variables)

    def add_sos2_constraint(self, variables):
        self._update()
        order = [i + 1 for i in range(len(variables))]
        self._prob.addSOS(gur.GRB.SOS_TYPE2, variables, order)

    def set_objective(self, obj):
        self._prob.setObjective(obj, gur.GRB.MINIMIZE)

    def get_value(self, var):
        if not self._solved:
            raise RuntimeError('Cannot take value since opt is not solved.')
        return var.x

    def solve(self):
        self._prob.optimize()
        self._solved = (self._prob.status == gur.GRB.OPTIMAL)


class Variable(object):
    """docstring for Variable"""
    def __init__(self, lb=0., ub=None, vtype='continuous', name=None):
        super(Variable, self).__init__()
        self._values = dict()
        self._name = name
        self._lb = lb
        self._ub = ub
        self._vtype = vtype

    def __setitem__(self, ix, val):
        self._values[ix] = val

    @property
    def fixed_indices(self):
        return self._values.keys()

    def to_series():
        return pd.Series(self._values)


    def get_expr(self, opt, ix):
        if self.is_fixed(ix):
            return self._values[ix]
        else:
            v = opt.vars[self]
            if not ix in v:
                if type(self._lb) is pd.Series:
                    lb = self._lb[ix]
                else:
                    lb = self._lb

                if type(self._ub) is pd.Series:
                    ub = self._ub[ix]
                else:
                    ub = self._ub

                v[ix] = opt.create_var(lb=lb, ub=ub,
                    vtype=self._vtype, name=self._name)
            return v[ix]

    def is_fixed(self, ix):
        return ix in self._values

    def fix_from(self, opt, ix):
        if not self.is_fixed(ix):
            self[ix] = opt.get_value(opt.vars[self][ix])
    
    def create_in(self, opt):
        if self not in opt.vars:
            opt.vars[self] = dict()

class SOS1Variables(Variable):
    """docstring for SOS1Variables """
    def __init__(self, n, vtype='continuous', **kwargs):
        super(SOS1Variables, self).__init__(**kwargs)
        self._n = n
        self._vtype = vtype

    def get_expr(self, opt, ix):
        if self.is_fixed(ix):
            return self._values[ix]
        else:
            v = opt.vars[self]
            if not ix in v:
                variables = [
                    opt.create_var(
                        vtype=self._vtype,
                        name=self._name + '[' + str(i) + '](' + str(ix) + ')') 
                    for i in range(self._n)]
                opt.add_sos1_constraint(variables)
                v[ix] = variables
            return v[ix]

    def fix_from(self, opt, ix):
        if not self.is_fixed(ix):
            self[ix] = [opt.get_value(var) for var in opt.vars[self][ix]]

class SOS2Variables(Variable):
    """docstring for SOS2Variables """
    def __init__(self, n, vtype='continuous'):
        super(SOS2Variables, self).__init__()
        self._n = n
        self._vtype = vtype

    def get_expr(self, opt, ix):
        if self.is_fixed(ix):
            return self._values[ix]
        else:
            v = opt.vars[self]
            if not ix in v:
                variables = [
                    opt.create_var(vtype=self._vtype) for i in range(self._n)]
                opt.add_sos2_constraint(variables)
                v[ix] = variables
            return v[ix]

    def fix_from(self, opt, ix):
        if not self.is_fixed(ix):
            self[ix] = [opt.get_value(var) for var in opt.vars[self][ix]]