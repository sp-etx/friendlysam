# coding=utf-8

from __future__ import division

import os.path

import matplotlib.pyplot as plt

from essim import datautil, visualization
import analysis
from . import Resources

HATCH_CYCLE = ['', '/', 'xx', '///', '\\', '\\\\\\']
COLOR_PAIR_CYCLE = [
    {'bg' : '#988ed5', 'fg' : '#303030'}, # purple
    {'bg' : '#777777', 'fg' : '#f0f0f0'}, # gray
    {'bg' : '#348abd', 'fg' : '#e0e0e0'}, # blue
    {'bg' : '#8eba42', 'fg' : '#ffffff'}, # green
    {'bg' : '#fbc15e', 'fg' : '#303030'}, # yellow
    {'bg' : '#ffb5b8', 'fg' : '#303030'}, # pink
    {'bg' : '#e24a33', 'fg' : '#e0e0e0'} # red
]


HEAT_PROD_AGGREGATES = [
    u'Renova CHP',
    u'Industrial waste heat',
    u'Rya heat pump',
    u'Sävenäs CHP',
    u'Rya CHP',
    u'Rya boiler',
    {
        'name' : u'Sävenäs boiler',
        'source_cols' : (
            u'Sävenäs boiler A',
            u'Sävenäs boiler B')
    },
    {
        'name' : u'Other',
        'source_cols' : (
            u'Rosenlund boiler B',
            u'Högsbo CHP',
            u'Rosenlund boiler A',
            u'Tynnered boiler',
            u'Angered boiler')
    }]

def fig_path(figdir, name):
    return os.path.join(figdir, name)

def save_stackplot_heat(f, figdir, name=None):
    if name is None:
        name = 'stacked_heat.png'

    title = 'Heat supply [MW]  -  Simulated'
    path = fig_path(figdir, name)

    production = analysis.get_production(f, Resources.heat)
    aggregated = datautil.aggregate_columns(production, HEAT_PROD_AGGREGATES)
    visualization.save_stackplot_fig(
        aggregated,
        fig_path(figdir, name),
        hatch_colors=[d['fg'] for d in COLOR_PAIR_CYCLE],
        hatches=HATCH_CYCLE,
        title=title)

def save_duration_heat(f, figdir, name=None):
    if name is None:
        name = 'duration_heat.png'

    path = fig_path(figdir, name)

    title = 'Simulated'

    production = analysis.get_production(f, Resources.heat)
    aggregated = datautil.aggregate_columns(production, HEAT_PROD_AGGREGATES)
    visualization.save_duration_fig(aggregated, path, title=title)


def save_stackplot_power(f, figdir, name=None):
    if name is None:
        name = 'stacked_power.png'

    title = 'Power supply [MW]'
    
    production = analysis.get_production(f, Resources.power)
    visualization.save_stackplot_fig(
        production,
        fig_path(figdir, name),
        hatch_colors=[d['fg'] for d in COLOR_PAIR_CYCLE],
        hatches=HATCH_CYCLE,
        title=title)

def save_duration_power(f, figdir, name=None):
    if name is None:
        name = 'duration_power.png'

    production = analysis.get_production(f, Resources.power)
    visualization.save_duration_fig(production, fig_path(figdir, name))


def save_barplot_heat(f, figdir, name=None):
    if name is None:
        name = 'bars_heat.png'

    production = analysis.get_production(f, Resources.heat)
    aggregated = datautil.aggregate_columns(production, HEAT_PROD_AGGREGATES)

    plotdata = aggregated.sum(axis=0)/1e3
    visualization.save_barplot_fig(
        plotdata,
        fig_path(figdir, name),
        title=u'District heating supply [GWh/year]')

def save_barplot_power(f, figdir, name=None):
    if name is None:
        name = 'bars_power.png'

    production = analysis.get_production(f, Resources.power)

    plotdata = production.sum(axis=0) / 1e3
    visualization.save_barplot_fig(
        plotdata,
        fig_path(figdir, name),
        title=u'Power supply [GWh/year]')