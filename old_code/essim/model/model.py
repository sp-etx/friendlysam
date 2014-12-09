# coding=utf-8

from __future__ import division

import h5py

from essim import datautil
import essim.core
from essim.core import EnergySystem, Storage, Cluster, ResourceNetwork
from . import LinearCHP, LinearSlowCHP, Boiler, Consumer, HeatPump, Import, Resources


PARAMETER_PATH_BASE = 'essim/model/parameters/'
RESULTS_PATH_BASE = 'essim/model/results/'
H5PY_READ = 'r' # 'r' means read

START_TIME = 1

def load_results(path):
    return h5py.File(path, H5PY_READ)

class Model(object):
    """docstring for Model"""

    save_types = (
        LinearCHP,
        LinearSlowCHP,
        Boiler,
        Consumer,
        HeatPump,
        Import,
        Storage)

    save_type_dict = {C.__name__ : C for C in save_types}

    def __init__(self, **kwargs):
        super(Model, self).__init__()

        #self._parameter_name = kwargs.pop('parameter_name')
        self.tmax = kwargs.pop('tmax')
        self.sched_hzn = kwargs.pop('sched_hzn')
        self.step = kwargs.pop('step')

        elements = kwargs.pop('elements')

        # Create one-cluster networks for heat and power
        heat_cluster = Cluster()
        power_cluster = Cluster()

        heat_cluster.add_elements(*
            [e for e in elements if Resources.heat in (e.inputs + e.outputs)])

        power_cluster.add_elements(*
            [e for e in elements if Resources.power in (e.inputs + e.outputs)])

        heat_grid = ResourceNetwork(Resources.heat, name=u'Heat grid')
        heat_grid.add_node(heat_cluster)

        power_grid = ResourceNetwork(Resources.power, name=u'Power grid')
        power_grid.add_node(power_cluster)

        self.energy_system = EnergySystem()
        self.energy_system.add_elements(heat_grid, power_grid)


    def run(self, update=None):
        self.energy_system.simulate(
            t0=START_TIME,
            tmax=self.tmax,
            step=self.step,
            sched_hzn=self.sched_hzn,
            update=update)
        
    def save_results(self, path):
        with h5py.File(path, 'w') as f: # 'w' means write and truncate if exists

            elements_group = f.require_group('Elements')
            save_times = range(START_TIME, self.tmax + 1)
            for e in self.energy_system.all_decendants:
                if isinstance(e, essim.core.Process):
                    g = elements_group.require_group(e.name)
                    datautil.save(e.name, 'name', g)
                    e.save_prod_cons(g, save_times)

    @staticmethod
    def load(path):
        with h5py.File(path, H5PY_READ) as f:

            params = datautil.load_dict(
                f['Model'],
                ('step', 'tmax', 'sched_hzn'))

            # Create elements
            elements = set()
            params['elements'] = elements
            for hdf5_group in f['Elements'].values():
                type_name = hdf5_group.attrs['type']

                if type_name in Model.save_type_dict:
                    T = Model.save_type_dict[type_name]
                    elements.add(T.load_from(hdf5_group))


        return Model(**params)
