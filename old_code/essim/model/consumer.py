from __future__ import division

import pandas as pd

from essim.core import *
from essim import datautil
from essim.model import Resources

class Consumer(LinearProcess):
    """docstring for Consumer"""
    def __init__(self, resource=None, demand=None, **kwargs):
        super(Consumer, self).__init__(**kwargs)
        self.consumption[resource] = self._demand
        self._resource = resource
        if demand is not None:
            for (t, val) in demand.iteritems():
                self._activity[t] = val


    def _demand(self, opt, t):
        return self._activity.get_expr(opt, t)

    @staticmethod
    def load_from(group):
        params = datautil.load_dict(group,
            ('resource', 'name'),
            optional=('demand',))
        params['resource'] = Resources[params['resource']]
        
        return Consumer(**params)

    def save_in(self, group):
        data = {}

        data['resource'] = self._resource.name
        data['demand'] = pd.Series(
            {t : self._demand(None, t) for t in self._activity.fixed_indices})
        data['name'] = self.name

        datautil.save_dict(data, group)

        