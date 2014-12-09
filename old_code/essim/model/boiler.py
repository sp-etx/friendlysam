from __future__ import division

from essim import datautil
from essim.core import *
from essim.model import Resources

class Boiler(LinearProcess):
    """docstring for Boiler"""
    def __init__(self, fuel=None, alpha=None, eta=None, Fmax=None,
        cost=None, **kwargs):
        
        kwargs['ub'] = Fmax
        super(Boiler, self).__init__(**kwargs)

        self.consumption[fuel] = self._F
        self.production[Resources.heat] = self._Q

        self._fuel = fuel
        self._eta = eta
        self._Fmax = Fmax
        self._cost = cost

    def _F(self, opt, t):
        return self._activity.get_expr(opt, t)

    def _Q(self, opt, t):
        return self._eta * self._F(opt, t)

    def get_cost_expr(self, opt, t):
        return self._cost * self._F(opt, t)

    @staticmethod
    def load_from(group):   
        params = datautil.load_dict(
            group,
            ('eta', 'Fmax', 'fuel', 'cost', 'name'))
        params['fuel'] = Resources[params['fuel']]

        return Boiler(**params)

    def save_in(self, group):
        data = {
            'eta' : self._eta,
            'Fmax' : self._Fmax,
            'fuel' : self._fuel.name,
            'cost' : self._cost,
            'name' : self.name
        }
        
        datautil.save_dict(data, group)
