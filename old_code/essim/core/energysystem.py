# coding=utf-8

from __future__ import division

import h5py

from optimization import OptimizationProblem
from element import Element
from storage import Storage
from process import Process
from resourcenetwork import ResourceNetwork

class EnergySystem(Element):
    """docstring for EnergySystem"""
    def __init__(self, **kwargs):
        super(EnergySystem, self).__init__(**kwargs)

    def simulate(self, t0=None, tmax=None, sched_hzn=None, step=None,
        update=None):
        all_decendants = self.all_decendants
        storages = [e for e in all_decendants if isinstance(e, Storage)]
        processes = [e for e in all_decendants if isinstance(e, Process)]
        networks = [e for e in all_decendants if isinstance(e, ResourceNetwork)]

        for s in storages:
            if not s.is_volume_fixed(t0):
                raise RuntimeError('Volume in storage "' + str(s) + 
                    '"" is not set at simulation start')

        for t in xrange(t0, tmax + 1, step):
            if update is not None:
                update((t-t0)/(tmax-t0))

            opt = OptimizationProblem(t, sched_hzn)
            self.setup_optimization_recursively(opt)
            total_cost = sum(
                [self.get_total_cost_expr(opt, tau) for tau in opt.times])
            opt.set_objective(total_cost)
            opt.solve()

            for tau in range(step):
                for s in storages:
                    s.fix_volume(opt, t+1+tau)
                for p in processes:
                    p.fix_activity(opt, t+tau)
                for n in networks:
                    n.fix_flows(opt, t+tau)

    def save_all_elements(self, filename, overwrite=False):
        mode = 'w' if overwrite else 'w-'
        with h5py.File(filename, mode) as ds:
            for element in self.all_elements:
                group_name = element.name
                group = ds.create_group(group_name)
                group.attrs['name'] = element.name
                element.save_in(group)

    def get_total_cost_expr(self, opt, t):
        return sum([e.get_cost_expr(opt, t) for e in self.all_decendants])
