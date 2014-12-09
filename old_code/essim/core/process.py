# coding=utf-8

from __future__ import division

import numpy as np
import pandas as pd

from element import Element
from optimization import Variable, SOS1Variables, SOS2Variables
from essim import datautil

MAX_ACTIVITY = 1e5

class Process(Element):
    """docstring for Process"""
    def __init__(self, **kwargs):
        super(Process, self).__init__(**kwargs)
        self.consumption = dict()
        self.production = dict()
        
    @property
    def inputs(self):
        return self.consumption.keys()

    @property
    def outputs(self):
        return self.production.keys()

    def save_prod_cons(self, group, save_times=None):
        times = self.fixed_times
        if save_times is not None:
            times = [t for t in times if t in save_times]

        prod_group = group.require_group('Production')
        for res in self.outputs:
            prod_series = pd.Series(
                data=[self.production[res](None, t) for t in times],
                index=times)
            datautil.save(prod_series, res.name, prod_group)

        prod_group = group.require_group('Consumption')
        for res in self.inputs:
            cons_series = pd.Series(
                data=[self.consumption[res](None, t) for t in times],
                index=times)
            datautil.save(cons_series, res.name, prod_group)
        

    def fix_activity(self, opt, t):
        pass
    
    @property
    def fixed_times(self):
        raise NotImplementedError('This is a responsibility of subclasses.')


class LinearProcess(Process):
    """docstring for LinearProcess"""
    def __init__(self, lb=0., ub=None, **kwargs):
        super(LinearProcess, self).__init__(**kwargs)

        varname = unicode(self) + ' activity'
        self._activity = Variable(lb=lb, ub=ub, name=varname)
        self._add_opt_setup(self._activity.create_in)

    def fix_activity(self, opt, t):
        super(LinearProcess, self).fix_activity(opt, t)
        self._activity.fix_from(opt, t)

    @property
    def fixed_times(self):
        return self._activity.fixed_indices


class PiecewiseAffineProcess(Process):
    """docstring for PiecewiseAffineProcess"""
    def __init__(self, n=None, **kwargs):
        super(PiecewiseAffineProcess, self).__init__(**kwargs)
        
        self._activity_weights = SOS2Variables(n)
        self._add_opt_setup(self._activity_weights.create_in)
        self._add_opt_setup(self._set_weight_constraints)

        self._add_save_func(self._save_weights)

    def fix_activity(self, opt, t):
        super(PiecewiseAffineProcess, self).fix_activity(opt, t)
        self._activity_weights.fix_from(opt, t)

    @property
    def fixed_times(self):
        return self._activity_weights.fixed_indices

    def _set_weight_constraints(self, opt):
        for t in opt.times:
            weights = self._activity_weights.get_expr(opt, t)
            opt.add_constraint(sum(weights) == 1)

    def _save_weights(self, group):
        times = self.fixed_times
        weights = np.array(
            [self._activity_weights.get_expr(None, t) for t in times])
        group.create_dataset('weights', data=weights)


class SlowProcess(Process):
    """docstring for SlowProcess"""
    def __init__(self, startup_time=None, **kwargs):
        super(SlowProcess, self).__init__(**kwargs)
        self.startup_time = startup_time

        #Off, Standby, On
        num_modes = 3
        self._modes = SOS1Variables(num_modes, name='mode')

        self._add_opt_setup(self._modes.create_in)

        #self._add_save_func(self._save_modes)

    def _off(self, opt, t):
        return self._modes.get_expr(opt, t)[0]

    def _standby(self, opt, t):
        return self._modes.get_expr(opt, t)[1]

    def _on(self, opt, t):
        return self._modes.get_expr(opt, t)[2]

    def _save_modes(self, group):
        times = self.fixed_times
        modes = np.array([self._modes.get_expr(None, t) for t in times])
        group.create_dataset('modes', data=modes)

    def fix_activity(self, opt, t):
        super(SlowProcess, self).fix_activity(opt, t)
        self._modes.fix_from(opt, t)


class LinearSlowProcess(LinearProcess, SlowProcess):
    """docstring for LinearSlowProcess"""
    def __init__(self, **kwargs):
        super(LinearSlowProcess, self).__init__(**kwargs)

        self._add_opt_setup(self._set_mode_constraints)

    def fix_activity(self, opt, t):
        super(LinearSlowProcess, self).fix_activity(opt, t)

    def _set_mode_constraints(self, opt):            
        for t in opt.times:

            # Exactly one mode at a time
            opt.add_constraint(sum(self._modes.get_expr(opt, t)) == 1)

            # Activity must be zero if not in "on" mode
            opt.add_constraint(
                self._activity.get_expr(opt, t) <= self._on(opt, t) * MAX_ACTIVITY)

            if self.startup_time > 0:
                # "on" mode only allowed only after a startup time in standby/on
                recent_sum = sum(
                    [self._on(opt, t-tau-1) + self._standby(opt, t-tau-1)
                    for tau in range(self.startup_time)])

                opt.add_constraint(
                    self._on(opt, t) <= recent_sum * (1/self.startup_time))



class PiecewiseAffineSlowProcess(PiecewiseAffineProcess, SlowProcess):
    """docstring for PiecewiseAffineSlowProcess"""
    def __init__(self, **kwargs):
        super(PiecewiseAffineSlowProcess, self).__init__(**kwargs)

        self._remove_opt_setup(self._set_weight_constraints)        
        self._add_opt_setup(self._set_mode_constraints)

    def fix_activity(self, opt, t):
        super(PiecewiseAffineSlowProcess, self).fix_activity(opt, t)

    def _set_mode_constraints(self, opt):
        for t in opt.times:

            # Exactly one mode at a time
            opt.add_constraint(sum(self._modes.get_expr(opt, t)) == 1)

            # Sum of activity weights is zero if not in "on" mode, one otherwise
            weights = self._activity_weights.get_expr(opt, t)
            opt.add_constraint(sum(weights) == self._on(opt, t))

            # "on" mode only allowed only after a startup time in standby/on
            recent_sum = sum(
                [self._on(opt, t-tau-1) + self._standby(opt, t-tau-1)
                for tau in range(self.startup_time)])

            opt.add_constraint(
                self._on(opt, t) <= recent_sum * (1/self.startup_time))

