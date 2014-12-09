from __future__ import division

import pandas as pd 

from essim import datautil
from essim.core import *
from essim.model import Resources

class LinearCHP(LinearProcess):
    """docstring for LinearCHP"""
    def __init__(self, fuel=None, alpha=None, eta=None, Fmax=None,
        cost=None, fuel_use=None, **kwargs):
        
        super(LinearCHP, self).__init__(ub=Fmax, **kwargs)

        self.consumption[fuel] = self._F
        self.production[Resources.heat] = self._Q
        self.production[Resources.power] = self._P

        self._fuel = fuel
        self._alpha = alpha
        self._eta = eta
        self._Fmax = Fmax
        self._cost = cost

        if fuel_use is not None:
            for (t, val) in fuel_use.iteritems():
                self._activity[t] = val

    def _F(self, opt, t):
        return self._activity.get_expr(opt, t)

    def _Q(self, opt, t):
        return (self._eta / (self._alpha + 1)) * self._F(opt, t)

    def _P(self, opt, t):
        return self._alpha * self._Q(opt, t)

    def get_cost_expr(self, opt, t):
        return self._cost * self._F(opt, t)

    
    @staticmethod
    def load_from(group):
        params = datautil.load_dict(
            group,
            ('eta', 'alpha', 'fuel', 'cost', 'name'),
            optional=('Fmax', 'fuel_use'))

        params['fuel'] = Resources[params['fuel']]

        return LinearCHP(**params)

    def save_in(self, group):

        data = {
            'eta' : self._eta,
            'alpha' : self._alpha,
            'fuel' : self._fuel.name,
            'cost' : self._cost,
            'Fmax' : self._Fmax,
            'fuel_use' : pd.Series(
                {t : self._F(None, t) for t in self._activity.fixed_indices}),
            'name' : self.name
        }

        datautil.save_dict(data, group)


class LinearSlowCHP(LinearSlowProcess):
    """docstring for LinearSlowCHP"""
    def __init__(self, fuel=None, alpha=None, eta=None, Fmin=None, Fmax=None, 
        cost=None, **kwargs):

        kwargs['ub'] = Fmax
        super(LinearSlowCHP, self).__init__(**kwargs)

        self.consumption[fuel] = self._F
        self.production[Resources.heat] = self._Q
        self.production[Resources.power] = self._P

        self._fuel = fuel
        self._alpha = alpha
        self._eta = eta
        self._Fmax = Fmax
        self._Fmin = Fmin
        self._cost = cost

        self._add_opt_setup(self._set_capacity_constraints)

    def _set_capacity_constraints(self, opt):
        if self._Fmin > 0:
            for t in opt.times:
                on_or_standby = 1 - self._off(opt, t)
                fuel_use = self.consumption[self._fuel](opt, t)
                opt.add_constraint(fuel_use >= self._Fmin * on_or_standby)

    def _productive_F(self, opt, t):
        return self._activity.get_expr(opt, t)

    def _standby_F(self, opt, t):
        return self._standby(opt, t) * self._Fmin

    def _F(self, opt, t):
        return self._productive_F(opt, t) + self._standby_F(opt, t)

    def _Q(self, opt, t):
        return (self._eta / (self._alpha + 1)) * self._productive_F(opt, t)

    def _P(self, opt, t):
        return self._alpha * self._Q(opt, t)

    def get_cost_expr(self, opt, t):
        return self._cost * self._F(opt, t)


    @staticmethod
    def load_from(group):
        params = datautil.load_dict(
            group,
            ('eta', 'alpha', 'fuel', 'cost', 
                'Fmin', 'Fmax', 'startup_time', 'name'))

        params['fuel'] = Resources[params['fuel']]

        chp_plant = LinearSlowCHP(**params)

        return chp_plant

    def save_in(self, group):
        data = {
            'eta' : self._eta,
            'alpha' : self._alpha,
            'fuel' : self._fuel.name,
            'cost' : self._cost,
            'Fmin' : self._Fmin,
            'Fmax' : self._Fmax,
            'startup_time' : self.startup_time,
            'name' : self.name
        }

        datautil.save_dict(data, group)



# class PiecewiseAffineSlowCHP(PiecewiseAffineSlowProcess):
#     """docstring for PiecewiseAffineSlowCHP"""
#     def __init__(self, fuel=None, Ps=None, etas=None, alpha=None,
#         cost=None, **kwargs):

#         # Assuming a piecewise affine relationship between F and P + Q

#         # eta * F = P + Q
#         # alpha * Q = P


#         Ps_plus_Qs = (1 + 1 / alpha) * np.array(Ps)
#         Fs = Ps_plus_Qs / np.array(etas)

#         self._Fs = Fs
#         self._Qs = Ps_plus_Qs / (1 + alpha)
#         self._Ps = self._Qs * alpha
#         self._cost = cost

#         n = len(Ps)

#         super(PiecewiseAffineSlowCHP, self).__init__(n=n, **kwargs)

#         self.production[Resources.heat] = self._Q
#         self.production[Resources.power] = self._P
#         self.consumption[fuel] = self._F


#     def _P(self, opt, t):
#         weights = self._activity_weights.get_expr(opt, t)
#         return dot(self._Ps, weights)

#     def _Q(self, opt, t):
#         weights = self._activity_weights.get_expr(opt, t)
#         return dot(self._Qs, weights)

#     def _F(self, opt, t):
#         weights = self._activity_weights.get_expr(opt, t)
#         productive_use = dot(self._Fs, weights)

#         Fmin = self._Fs[0]
#         standby_use = self._standby(opt, t) * Fmin
        
#         return productive_use + standby_use

#     def get_cost_expr(self, opt, t):
#         return self._cost * self._F(opt, t)
