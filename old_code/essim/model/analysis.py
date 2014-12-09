# coding=utf-8

from __future__ import division

import pandas as pd

from essim import datautil
from . import Model, Resources

EMISSION_FACTORS = {} #kg CO2e/MWh
EMISSION_FACTORS[Resources.heating_oil] = 280
EMISSION_FACTORS[Resources.natural_gas] = 220
EMISSION_FACTORS[Resources.msw] = 144.
EMISSION_FACTORS[Resources.biofuel] = 0.
#EMISSION_FACTORS[Resources.power] = 476. #imported power EU27 mean
EMISSION_FACTORS[Resources.power] = 125.5 #imported power Nordic mean

def get_production(h5_file, resource):
    data = {}
    for e in h5_file['Elements']:
        prod_group = h5_file['Elements'][e]['Production']
        if resource.name in prod_group:
            element_name = h5_file['Elements'][e]['name'][()]
            data[element_name] = datautil.load(prod_group[resource.name])

    return pd.DataFrame.from_dict(data)

def get_consumption(h5_file, resource):
    data = {}
    for e in h5_file['Elements']:
        cons_group = h5_file['Elements'][e]['Consumption']
        if resource.name in cons_group:
            element_name = h5_file['Elements'][e]['name'][()]
            data[element_name] = datautil.load(cons_group[resource.name])

    return pd.DataFrame.from_dict(data)

def get_energy_input(h5_file):
    inputs = {}

    fuels = (
        Resources.heating_oil,
        Resources.natural_gas,
        Resources.msw,
        Resources.biofuel)
    
    for f in fuels:
        inputs[f.name] = get_consumption(h5_file, f).sum().sum()

    for p in ('Power import', 'Wind power'):
        inputs[p] = datautil.load(
            h5_file['Elements'][p]['Production'][Resources.power.name]).sum()

    return pd.Series(inputs)

def get_ghg_emissions(h5_file):
    fuels = (
        Resources.heating_oil,
        Resources.natural_gas,
        Resources.msw,
        Resources.biofuel)

    emissions = {}

    for f in fuels:
        emissions[f.name] = (
            get_consumption(h5_file, f).sum().sum() * EMISSION_FACTORS[f])

    emissions['Power import'] = datautil.load(
        h5_file['Elements']['Power import']['Production'][Resources.power.name]
        ).sum() * EMISSION_FACTORS[Resources.power]

    return pd.Series(emissions)

def get_heat_breakdown(h5_file):
    prod = get_production(h5_file, Resources.heat)
    return prod.sum(axis=0)

    