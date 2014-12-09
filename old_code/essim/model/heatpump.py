from __future__ import division

from essim.core import *
from essim.model import Resources
from essim import datautil

class HeatPump(LinearProcess):
    """docstring for HeatPump"""
    def __init__(self, COP=None, Qmax=None, cost=None, **kwargs):
        kwargs['ub'] = Qmax
        super(HeatPump, self).__init__(**kwargs)

        self.consumption[Resources.power] = self._P
        self.production[Resources.heat] = self._Q

        self._COP = COP
        self._Qmax = Qmax
        self._cost = cost

    def _Q(self, opt, t):
        return self._activity.get_expr(opt, t)

    def _P(self, opt, t):
        return self._Q(opt, t) * (1 / self._COP)

    def get_cost_expr(self, opt, t):
        return self._cost * self._P(opt, t)

    @staticmethod
    def load_from(group):
        params = datautil.load_dict(
            group, 
            ('COP', 'Qmax', 'cost', 'name'))

        return HeatPump(**params)

    def save_in(self, group):
        data = {
            'name' : self.name,
            'COP' : self._COP,
            'Qmax' : self._Qmax,
            'cost' : self._cost
        }

        datautil.save_dict(data, group)