# coding=utf-8

from __future__ import division

import numpy as np
import pandas as pd

from friendlysam.parts import Part


class Storage(Part):
    """docstring for Storage"""
    def __init__(self, resource=None, capacity=None, maxchange=None, **kwargs):
        super(Storage, self).__init__(**kwargs)
        self.resource = resource

        self._capacity = capacity
        self._volume = Variable(lb=0., ub=capacity)
        self._add_opt_setup(self._volume.create_in)

        self._maxchange = maxchange
        if maxchange is not None:
            self._add_opt_setup(self._set_maxchange_constraints)
            
        self._add_save_func(self._save_volume)

    @property
    def inputs(self):
        return [self.resource]

    @property
    def outputs(self):
        return [self.resource]    

    def volume(self, opt, t):
        return self._volume.get_expr(opt, t)

    def is_volume_fixed(self, t):
        return self._volume.is_fixed(t)

    def fix_volume(self, opt, t):
        self._volume.fix_from(opt, t)

    def set_volume(self, t, volume):
        self._volume[t] = volume

    def get_accumulation(self, opt, t):
        return self.volume(opt, t+1) - self.volume(opt, t)

    def _get_storage_times(self, opt):
        times = list(opt.times)
        times.append(opt.t0 + opt.timespan)
        return times

    def _set_maxchange_constraints(self, opt):
        for t in opt.times:
            opt.add_range(
                self.get_accumulation(opt, t),
                -self._maxchange,
                self._maxchange)

    @staticmethod
    def load_from(group):
        params = load_dict(
            group, 
            required=('resource', 'capacity', 'name'),
            optional=('max_change',))

        params['resource'] = Resources[params['resource']]

        s = Storage(**params)

        if 'volume' in group:
            for row in group['volume']:
                s.set_volume(row['time'], row['volume'])



    def save_in(self, group):
        data = {
            'resource' : self.resource.name,
            'capacity' : self._capacity,
            'maxchange' : self._maxchange,
            'volume' : self._volume.to_series(),
            'name' : self.name
        }

        datautil.save_dict(data, group)