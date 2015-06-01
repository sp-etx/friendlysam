# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
from copy import deepcopy

import pandas as pd
import numpy as np

import friendlysam as fs
from partlib import Resources, HeatPump, Import, LinearCHP, LinearSlowCHP, Boiler

data_dir = 'data'

def get_heat_history(time_unit):
    heat_history = pd.read_csv(
        'data/heat_history.csv',
        encoding='utf-8',
        index_col='Time (UTC)',
        parse_dates=True)
    return heat_history.resample(time_unit, how='sum')

def get_power_demand(time_unit):
    power_demand = pd.read_csv(
        'data/power_demand.csv',
        encoding='utf-8',
        index_col='Time (UTC)',
        parse_dates=True,
        squeeze=True)
    return power_demand.resample(time_unit, how='sum')

def get_power_price(time_unit):
    power_price = pd.read_csv(
        'data/power_price.csv',
        encoding='utf-8',
        index_col='Time (UTC)',
        parse_dates=True,
        squeeze=True)
    return power_price.resample(time_unit, how='mean')



_DEFAULT_PARAMETERS = {
    't0': pd.Timestamp('2013-01-01'),
    'time_unit' : pd.Timedelta('12h'), # Time unit
    'step' : pd.Timedelta('12h'), # Time span to lock in each step
    'horizon' : pd.Timedelta('12h'), # Planning horizon
    'prices': {
        Resources.heating_oil: 500, # SEK/MWh (LHV)
        Resources.bio_oil: 500, # SEK/MWh (LHV)
        Resources.natural_gas: 280, # SEK/MWh (LHV)
        Resources.wood_chips: 200, # SEK/MWh (LHV)
        Resources.wood_pellets: 320, # SEK/MWh (LHV)
    },
    'green_certificates': {
        'price': 200, # SEK/MWh
        'quota': .15
    }
}

def get_parameters(**kwargs):
    parameters = deepcopy(_DEFAULT_PARAMETERS)
    parameters.update(kwargs)
    return parameters


def make_model(parameters, seed=None):
    uncertain = DummyRandomizer() if seed is None else Randomizer(seed)
    parameters['prices'][Resources.power] = get_power_price(parameters['time_unit'])

    model = fs.models.MyopicDispatchModel(
        t0=parameters['t0'],
        horizon=int(parameters['horizon'] / parameters['time_unit']),
        step=int(parameters['step'] / parameters['time_unit']))

    parts = make_parts(parameters, uncertain)

    def step_time(t, step):
        return t + step * parameters['time_unit']

    # No explicit distribution channels in this model. Just create a cluster for each resource.
    for r in Resources:
        cluster = fs.Cluster(resource=r, name='{} cluster'.format(r))
        cluster.add_parts(*(p for p in parts if r in p.resources))
        model.add_part(cluster)

    for p in model.descendants_and_self:
        p.step_time = step_time

    return model


def make_parts(parameters, uncertain):
    parts = set()

    heat_history = get_heat_history(parameters['time_unit'])
    power_demand = get_power_demand(parameters['time_unit'])
    taxation = make_tax_function(parameters)

    for r in Resources:
        if r is not Resources.heat:
            parts.add(
                Import(
                    resource=r,
                    price=parameters['prices'][r],
                    name='Import({})'.format(r)))

    # Conversion factor from hour to model time unit:
    # "hour" is the number of model time steps per hour.
    # So when capacities/consumption/etc per time step in plants below are stated like
    # "600 / hour", then think "600 MWh per hour".
    # Makes sense because
    #   larger time unit --> smaller value of "hour" --> larger max output per time step.
    hour = pd.Timedelta('1h') / parameters['time_unit']

    series_reader = lambda series: series.loc.__getitem__
    city = fs.Node(name='City')
    city.consumption[Resources.heat] = series_reader(heat_history.sum(axis=1))
    city.consumption[Resources.power] = series_reader(power_demand)
    city.cost = lambda t: 0
    city.state_variables = lambda t: ()
    parts.add(city)

    solid_waste_incineration = fs.Node(name='Renova CHP')
    solid_waste_incineration.production[Resources.heat] = series_reader(heat_history['Renova CHP'])
    solid_waste_incineration.cost = lambda t: 0
    solid_waste_incineration.state_variables = lambda t: ()
    parts.add(solid_waste_incineration)

    parts.add(
        LinearSlowCHP(
            name='Rya CHP',
            eta=uncertain.relative(0.925, 0.03),
            alpha=uncertain.relative(0.86, 0.05),
            Fmax=uncertain.relative(600, 0.05) / hour,
            Fmin=uncertain.relative(600 * 0.20, 0.3) / hour,
            start_steps=int(np.round(.5 * hour)),
            fuel=Resources.natural_gas,
            taxation=taxation))

    parts.add(
        LinearSlowCHP(
            name='Sävenäs CHP',
            eta=uncertain.relative(1.07, 0.05),
            alpha=uncertain.relative(0.08, 0.2),
            Fmax=uncertain.relative(130, 0.1) / hour,
            Fmin=uncertain.relative(130 * 0.3, 0.5) / hour,
            start_steps=int(np.round(uncertain.absolute(6, -4, 6) * hour)),
            fuel=Resources.wood_chips,
            taxation=taxation))

    parts.add(
        Import(
            name='Industrial waste heat',
            resource=Resources.heat,
            capacity=uncertain.relative(140, 0.2) / hour,
            price=0))
    # Waste heat price is not actually zero, but we can assume that it is always cheaper
    # than other source, so results should be reasonable if we set cost == 0.

    parts.add(
        HeatPump(
            name='Rya heat pump',
            COP=uncertain.absolute(3.3, 0.2),
            Qmax=uncertain.relative(100, 0.2) / hour,
            taxation=taxation))

    parts.add(
        LinearCHP(
            name='Högsbo CHP',
            eta=uncertain.relative(0.85, 0.05),
            alpha=uncertain.relative(0.8, 0.05),
            Fmax=uncertain.relative(34, 0.1) / hour,
            fuel=Resources.natural_gas,
            taxation=taxation))

    parts.add(
        Boiler(
            name='Sävenäs boiler A',
            eta=uncertain.relative(1.03, 0.05),
            Fmax=uncertain.relative(89, 0.1) / hour,
            fuel=Resources.natural_gas,
            taxation=taxation))

    parts.add(
        Boiler(
            name='Sävenäs boiler B',
            eta=uncertain.relative(0.89, 0.05),
            Fmax=uncertain.relative(89, 0.1) / hour,
            fuel=Resources.natural_gas,
            taxation=taxation))

    parts.add(
        Boiler(
            name='Rosenlund boiler B',
            eta=uncertain.relative(0.93, 0.05),
            Fmax=155 / hour,
            fuel=Resources.natural_gas,
            taxation=taxation))

    parts.add(
        Boiler(
            name='Rosenlund boiler A',
            eta=uncertain.relative(0.9, 0.05),
            Fmax=uncertain.relative(465, 0.1) / hour,
            fuel=Resources.heating_oil,
            taxation=taxation ))

    parts.add(
        Boiler(
            name='Rya boiler',
            eta=uncertain.relative(0.87, 0.05),
            Fmax=uncertain.relative(115, 0.1) / hour,
            fuel=Resources.wood_pellets,
            taxation=taxation))

    parts.add(
        Boiler(
            name='Tynnered boiler',
            eta=uncertain.relative(0.9, 0.05),
            Fmax=uncertain.relative(22, 0.2) / hour,
            fuel=Resources.heating_oil,
            taxation=taxation))

    parts.add(
        Boiler(
            name='Angered boiler',
            eta=uncertain.relative(0.9, 0.05),
            Fmax=uncertain.relative(137, 0.1) / hour,
            fuel=Resources.bio_oil,
            taxation=taxation))

    return parts


def make_tax_function(parameters):
    def net_tax(cons_or_prod=None, resource=None, **kwargs):
        # Net taxes (taxes - subsidies) for consumption or production of energy
        # In unit SEK/MWh (lower heating value where applicable)

        if resource not in Resources:
            raise ValueError('resource {} does not exist'.format(resource))

        is_biofuel = lambda r: (
            r is Resources.bio_oil or 
            r is Resources.wood_chips or
            r is Resources.wood_pellets)

        if cons_or_prod == 'consumption':
            if resource is Resources.power:
                energy_tax = 294 # SEK / MWh as of 2015-01-01, most Swedish municipalities
                cert = parameters['green_certificates']
                cert_cost = cert['price'] * cert['quota']
                return energy_tax * cert_cost
            if is_biofuel(resource):
                return 0
            if resource is Resources.natural_gas:
                carbon_tax = 2.409 # 2409 SEK / 1000 m^3 as of 2015-01-01
                energy_tax = 939 # 939 SEK / 1000 m^3 as of 2015-01-01
                if kwargs['chp']:
                    carbon_tax *= 0 # As of 2013
                    energy_tax *= 0.3 # As of 2013
                else:
                    carbon_tax *= .8 # As of 2014, for other heat production if included in EU ETS
                tax = (carbon_tax + energy_tax) / (10.9 / 1000) # LHV: 10.9 kWh / m^3 
                return tax
            if resource is Resources.heating_oil:
                # Assuming heating oil means Swedish "Eldningsolja 5"
                carbon_tax = 3218 # 3218 SEK / m^3 as of 2015-01-01
                energy_tax = 850 # 850 SEK / m^3 as of 2015-01-01 for tax reduced heating oil
                if kwargs['chp']:
                    carbon_tax *= 0 # As of 2013
                    energy_tax *= 0.3 # As of 2013
                else:
                    carbon_tax *= .8 # As of 2014, for other heat production if included in EU ETS
                tax = (carbon_tax + energy_tax) / (955 * 11.4 / 1e3) # Density 955 kg/m^3 LHV: 11.4 kWh / kg
                return tax
            raise ValueError('Resource {} not supported'.format(resource))
        
        if cons_or_prod == 'production':
            if resource is Resources.power:
                renewable = is_biofuel(kwargs['fuel'])
                return -parameters['green_certificates']['price'] if renewable else 0
            else:
                return 0

        raise ValueError("cons_or_prod should be 'consumption' or 'production'")

    return net_tax


class Randomizer(object):
    """docstring for Randomizer"""
    def __init__(self, seed):
        super().__init__()
        self._random_state = np.random.RandomState(seed)


    def relative(self, value, *args, **kwargs):
        return value * self.factor(*args, **kwargs)


    def absolute(self, value, *args, **kwargs):
        return value + self.term(*args, **kwargs)


    def factor(self, a, b=None):
        if b is None:
            low, high = 1 - a, 1 + a
        else:
            low, high = a, b

        return self._random_state.uniform(low, high)


    def term(self, a, b=None):
        if b is None:
            low, high = -a, a
        else:
            low, high = a, b
        return self._random_state.uniform(low, high)

class DummyRandomizer(object):
    """docstring for DummyRandomizer"""

    def _do_nothing(value, *args, **kwargs):
        return value

    relative = _do_nothing
    absolute = _do_nothing

    def factor(self, *args, **kwargs):
        return 1

    def term(self, *args, **kwargs):
        return 0

if __name__ == '__main__':
    parameters = get_parameters()
    m = make_model(parameters, seed=1)
    m.solver = fs.get_solver()
    m.advance()
    for p in m.descendants:
        logger.info(p)
        for r in p.resources:
            for k in ('production', 'consumption', 'accumulation'):
                t_m_1 = p.step_time(m.t, -1)
                attr = getattr(p, k)
                if r in attr:
                    logger.info('\t{}[{}] ({}): {}'.format(k, r, t_m_1, float(attr[r](t_m_1))))