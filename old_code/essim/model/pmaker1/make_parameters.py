# coding=utf-8

from __future__ import division

import copy

import h5py
import json
import pandas as pd
import numpy as np

import essim.data.heat
import essim.data.power
import essim.data.nordpool
from essim import datautil
from essim.model import Resources
from essim.model import LinearCHP, LinearSlowCHP, Boiler, HeatPump, Import, Consumer
from essim.core import Storage

DEFAULTS = {
    'seed' : 1,
    'step' : 12, # model time units to lock per simulation step
    'time_res' : 2, # time resolution in hours
    'sched_hzn_hours' : 72, # in hours
    'tmax_hours' : 8760, # hours
    'base_year' : 2012,
    'constant_power_price' : False,
    'power_price_factor' : 1.,
    'tax_NG_CHP' : 24, #SEK/MWh(LHV)
    'tax_NG_heat' : 250, #SEK/MWh(LHV)
    'tax_oil_heat' : 300, #SEK/MWh(LHV)
    'prices/heating_oil' : 500, #SEK/MWh(LHV)
    'prices/bio_oil' : 500, #SEK/MWh(LHV)
    'prices/natural_gas' : 280, #SEK/MWh(LHV)
    'prices/wood_chips' : 200, #SEK/MWh(LHV)
    'prices/wood_pellets' : 320, #SEK/MWh(LHV)
    'prices/green_certificates' : 200, #SEK/MWh
    'electricity_tax' : 180, #SEK/MWh
    'certificate_quota' : 0.15,
    'mean_wind_power' : 80.e3 / 8760, # MW
    'mean_power_use' : 4407 * 10**3 / 8760, #MW, Bilaga Klimatprogrammet
    'heat_pump_Qmax' : 100, #MW
    'waste_heat_max' : 150,
    'dh_base' : 170, #MW
    'dh_rel_demand' : 1., #relative to historical
    'power_rel_demand' : 1., #relative to historical
    'fossil_allowed' : True,
    'randomize' : True
}


def make_parameters(path, **kwargs):

    settings = copy.deepcopy(DEFAULTS)
    for key in kwargs:
        settings[key] = kwargs[key]

    random_state = np.random.RandomState(settings['seed'])

    def rfactor(a, b=None):
        if b is None:
            low, high = 1 - a, 1 + a
        else:
            low, high = a, b

        if settings['randomize'] is True:
            return random_state.uniform(low, high)
        else:
            return 1.

    def rterm(low, high):
        if settings['randomize'] is True:
            return random_state.uniform(low, high)
        else:
            return 0.

    settings['rfactor'] = rfactor
    settings['rterm'] = rterm

    settings['sched_hzn_hours'] *= rfactor(0.4)
    settings['prices/heating_oil'] *= rfactor(0.1)
    settings['prices/bio_oil'] *= rfactor(0.1)
    settings['prices/natural_gas'] *= rfactor(0.1)
    settings['prices/wood_chips'] *= rfactor(0.1)
    settings['prices/wood_pellets'] *= rfactor(0.1)
    settings['prices/green_certificates'] *= rfactor(0.1)
    settings['certificate_quota'] *= rfactor(0.2)
    settings['mean_power_use'] *= rfactor(0.05)
    settings['mean_wind_power'] *= rfactor(0.10)
    settings['heat_pump_Qmax'] *= rfactor(0.2)
    settings['waste_heat_max'] *= rfactor(0.1)
    settings['dh_base'] *= rfactor(0.1)


    settings['sched_hzn'] = int(
        settings['sched_hzn_hours'] / settings['time_res'])
    settings['tmax'] = int(settings['tmax_hours'] / settings['time_res'])

    elements = define_elements(settings)

    with h5py.File(path, 'w') as f: # 'w' means write and truncate if exists

        # Save some basic model settings
        mdl_grp = f.require_group('Model')
        save_keys = ('sched_hzn', 'tmax', 'step')
        datautil.save_dict({key : settings[key] for key in save_keys}, mdl_grp)

        # Save all the elements
        elements_group = f.require_group('Elements')
        for e in elements:
            g = elements_group.require_group(e.name)
            e.save_in(g)
            g.attrs['type'] = type(e).__name__

def adapt_history(
    history, ref_year=None, time_res=None, times=None, how='mean'):
    history_start = pd.datetime(ref_year, 1, 1)
    history = history.loc[history_start:]

    freq_string = str(time_res) + 'H'
    history = history.resample(freq_string, how=how)

    history = history.iloc[0:len(times)]
    history.index = times

    return history

def normalize_series(series, reference_length):
    #Normalize a series so that the first (reference_length) values have
    #series.iloc[0:reference_length].mean() == 1.
    return series / series.iloc[0:reference_length].mean()


def define_elements(settings):

    rfactor = settings['rfactor']
    rterm = settings['rterm']

    elements = list()

    fossil_allowed = settings['fossil_allowed']

    # Historical data range
    history_length = settings['tmax'] + settings['sched_hzn'] + 1
    times = np.arange(1, history_length+1, dtype=int)

    heat_history = adapt_history(
        essim.data.heat.get_history('essim/data/heat_plants_3.json'),
        settings['base_year'],
        times=times,
        time_res=settings['time_res'],
        how='sum')

    power_history_SE = adapt_history(
        essim.data.power.load_history(),
        settings['base_year'],
        times=times,
        time_res=settings['time_res'],
        how='sum')

    power_price_history = adapt_history(
        essim.data.nordpool.load_history()['SE2'],
        settings['base_year'],
        times=times,
        time_res=settings['time_res'],
        how='mean')


    renova_eta = 0.95 * rfactor(0.03)
    renova_alpha = 0.14 * rfactor(0.1)
    elements.append(
        LinearCHP(
            name=u'Renova CHP',
            eta=renova_eta,
            alpha=renova_alpha,
            fuel=Resources.msw,
            cost=0,
            fuel_use=heat_history[u'Renova CHP'] * (1 + renova_alpha) / renova_eta))

    elements.append(
        LinearSlowCHP(
            name = u'Rya CHP',
            eta = 0.925 * rfactor(0.03),
            alpha = 0.86 * rfactor(0.05),
            Fmax = (600 * rfactor(0.05) * settings['time_res'] * 
                (1 if fossil_allowed else 0)),
            Fmin = 600 * 0.20 * rfactor(0.3) * settings['time_res'],
            startup_time = int(np.round(1. / settings['time_res'])),
            fuel = Resources.natural_gas,
            cost = settings['prices/natural_gas'] + settings['tax_NG_CHP']))

    eta = 1.07 * rfactor(0.05)
    alpha = 0.08 * rfactor(0.2)
    certificate_income = ((eta * alpha / (1 + alpha)) *
        settings['prices/green_certificates'])
    elements.append(
        LinearSlowCHP(
            name = u'Sävenäs CHP',
            eta = eta,
            alpha = alpha,
            Fmin = 130*0.3 * settings['time_res'] * rfactor(0.5),
            Fmax = 130 * settings['time_res'] * rfactor(0.1),
            startup_time = int(np.round((6 + rterm(-4, 6)) / settings['time_res'])), #hours
            fuel = Resources.biofuel, #flis + lite bioolja
            cost = settings['prices/wood_chips'] - certificate_income))

    elements.append(
        LinearCHP(
            name = u'Högsbo CHP',
            eta = 0.85 * rfactor(0.05),
            alpha = 0.8 * rfactor(0.05),
            Fmax = (34 * settings['time_res'] * rfactor(0.1) *
                (1 if fossil_allowed else 0)),
            fuel = Resources.natural_gas,
            cost = settings['prices/natural_gas'] + settings['tax_NG_CHP']))

    elements.append(
        Boiler(
            name = u'Sävenäs boiler A',
            eta = 1.03 * rfactor(0.05),
            Fmax = (89 * settings['time_res'] * rfactor(0.1) *
                (1 if fossil_allowed else 0)),
            fuel = Resources.natural_gas,
            cost = settings['prices/natural_gas'] + settings['tax_NG_heat']))

    elements.append(
        Boiler(
            name = u'Sävenäs boiler B',
            eta = 0.89 * rfactor(0.05),
            Fmax = (89 * settings['time_res'] * rfactor(0.1) *
                (1 if fossil_allowed else 0)),
            fuel = Resources.natural_gas,
            cost = settings['prices/natural_gas'] + settings['tax_NG_heat']))

    elements.append(
        Boiler(
            name = u'Rosenlund boiler B',
            eta = 0.93 * rfactor(0.05),
            Fmax = 155 * settings['time_res'] * (1 if fossil_allowed else 0),
            fuel = Resources.natural_gas,
            cost = settings['prices/natural_gas'] + settings['tax_NG_heat']))

    elements.append(
        Boiler(
            name = u'Rosenlund boiler A',
            eta = 0.9 * rfactor(0.05),
            Fmax = (465 * settings['time_res'] * rfactor(0.1) *
                (1 if fossil_allowed else 0)),
            fuel = Resources.heating_oil,
            cost = settings['prices/heating_oil'] + settings['tax_oil_heat']))

    elements.append(
        Boiler(
            name = u'Rya boiler',
            eta = 0.87 * rfactor(0.05),
            Fmax = 115 * settings['time_res'] * rfactor(0.1),
            fuel = Resources.biofuel,
            cost = settings['prices/wood_pellets'])) #pellets + lite naturgas

    elements.append(
        Boiler(
            name = u'Tynnered boiler',
            eta = 0.9 * rfactor(0.05),
            Fmax = (22 * settings['time_res'] * rfactor(0.2) *
                (1 if fossil_allowed else 0)),
            fuel = Resources.heating_oil,
            cost = settings['prices/heating_oil'] + settings['tax_oil_heat']))

    elements.append(
        Boiler(
            name = u'Angered boiler',
            eta = 0.9 * rfactor(0.05),
            Fmax = 137 * settings['time_res'] * rfactor(0.1),
            fuel = Resources.biofuel,
            cost = settings['prices/bio_oil']))

    elements.append(
        Import(
            name = u'Industrial waste heat',
            resource = Resources.heat,
            max_import = settings['waste_heat_max'] * settings['time_res'],
            max_export = 0,
            cost = 0))

    rya_HP_COP = 3.3 + rterm(-0.2, 0.2)
    elements.append(
        HeatPump(
            name = u'Rya heat pump',
            COP = rya_HP_COP,
            #Qmax = heat_history['Rya heat pump'],
            Qmax = settings['heat_pump_Qmax'] * settings['time_res'],
            cost = (settings['certificate_quota'] * 
                settings['prices/green_certificates'] +
                settings['electricity_tax'])))

    # Q_t = b + h_t
    # Q*_t = b + h*_t
    # require that
    # sum_t Q*_t = T * b + sum_t h*_t = k * sum_t Q_t = k * b * T + k * sum_t h_t
    # and require that
    # h*_t = c * h_t
    # ==>
    # b * T * (1 - k) = sum_t (h_t - h*_t) = (k - c) * sum_t h_t
    # ==>
    # c = k - b * T * (1 - k) / sum_t h_t = k - b * (1 - k) / mean(h_t)

    k = settings['dh_rel_demand']
    b = settings['dh_base'] * settings['time_res']
    h = heat_history.sum(axis=1) - b
    c = k - b * (1. - k) / h.mean()
    dh_demand = b + c * h

    elements.append(
        Consumer(
            name = u'District heating demand',
            resource = Resources.heat,
            demand = dh_demand))


    #Power use in heat pumps
    heat_pump_use = heat_history[u'Rya heat pump'] / rya_HP_COP #MW averages

    #Power demand excluding heat pump use
    power_use_SE = power_history_SE[u'Total förbrukning']
    city_power_demand = (settings['time_res'] * settings['mean_power_use'] * 
        normalize_series(power_use_SE, settings['tmax'])
        - heat_pump_use) * settings['power_rel_demand']

    elements.append(
        Consumer(
            name = u'Power demand',
            resource = Resources.power,
            demand = city_power_demand))

    
    if settings['constant_power_price']:
        power_price = (
            (power_use_SE * power_price_history).sum() /
            power_use_SE.sum()) * settings['power_price_factor']
    else:
        power_price = power_price_history * settings['power_price_factor']

    elements.append(
        Import(
            name = u'Power import',
            resource = Resources.power,
            cost = power_price))

    wind_history_SE = power_history_SE[u'Vindkraft']
    wind_power_delivery = (settings['time_res'] * settings['mean_wind_power'] * 
        normalize_series(wind_history_SE, settings['tmax']))

    elements.append(
        Import(
            name = u'Wind power',
            resource = Resources.power,
            cost = 0,
            amount = wind_power_delivery))

    return elements

        