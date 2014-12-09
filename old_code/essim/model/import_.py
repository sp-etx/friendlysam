from __future__ import division

import pandas as pd

from essim.core import *
from essim import datautil
from essim.model import Resources


class Import(LinearProcess):
    """docstring for Import"""
    def __init__(self, resource=None, max_import=None, 
        max_export=None, cost=None, amount=None, **kwargs):
        if max_export is not None:
            kwargs['lb'] = -max_export
        if max_import is not None:
            kwargs['ub'] = max_import
        super(Import, self).__init__(**kwargs)

        self.production[resource] = self._import

        self._resource = resource
        self._max_import = max_import
        self._max_export = max_export
        self._cost = cost

        if amount is not None:
            for (t, val) in amount.iteritems():
                self._activity[t] = val

    def _import(self, opt, t):
        return self._activity.get_expr(opt, t)

    def get_cost_expr(self, opt, t):
        if type(self._cost) is pd.Series:
            cost = self._cost[t]
        else:
            cost = self._cost
            
        return cost * self._import(opt, t)

    @staticmethod
    def load_from(group):
        params = datautil.load_dict(
            group,
            required=('resource', 'cost', 'name'),
            optional=('max_export', 'max_import', 'amount'))

        params['resource'] = Resources[params['resource']]

        imp = Import(**params)

        return imp

    def save_in(self, group):
        amount = pd.Series(
            {t : self._import(None, t) for t in self._activity.fixed_indices})
        data = {
            'name' : self.name,
            'resource' : self._resource.name,
            'max_export' : self._max_export,
            'max_import' : self._max_import,
            'amount' : amount,
            'cost' : self._cost
        }

        datautil.save_dict(data, group)