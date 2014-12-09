#coding=utf-8
from __future__ import division
import matplotlib as mpl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mpltools.style
import itertools
import datetime
import matplotlib.dates
import matplotlib.cbook as cbook

COLORMAP = 'Paired'
FIGSIZE = (20/2.5, 14/2.5)
LABELS_ANGLE = 30

NUM_HOURS = 8760

mpltools.style.use(['ggplot', 'style2'])

def get_dates(hours, year=2001):
    start_date = datetime.date(year, 1, 1)
    return [start_date + datetime.timedelta(hours=(h-1)) for h in hours]

def format_year_xaxis(fig, ax):
    months   = matplotlib.dates.MonthLocator(bymonth=range(1,13,2))
    months_fmt = matplotlib.dates.DateFormatter('%b')

    # format the ticks
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(months_fmt)

    fig.autofmt_xdate()


def save_stackplot_fig(df, path, hatches=None, hatch_colors=None, title=None):

    time_res = NUM_HOURS / len(df.index)

    fig, ax = plt.subplots(1, 1)
    fig.set_size_inches((10/2.5, 9/2.5))

    plotdata = df.values / time_res

    times = np.arange(len(df.index.values)) * time_res

    leg = stackplot(
        ax,
        get_dates(times),
        plotdata.T,
        hatches=hatches,
        hatch_colors=hatch_colors,
        labels=df.columns.values.tolist())

    format_year_xaxis(fig, ax)

    ax.set_ylim(0,1200.)

    suptitle = None
    if title is not None:
        suptitle = fig.suptitle(title)

    if suptitle is not None:
        extra_artists=(leg, suptitle)
    else:
        extra_artists=(leg,)
    fig.savefig(path, bbox_extra_artists=extra_artists, bbox_inches='tight')

    plt.close(fig)


def stackplot(ax, x, *args, **kwargs):
    if not 'color' in kwargs:
        kwargs['linewidth'] = 0

    hatches = kwargs.pop('hatches', None)
    hatch_colors = kwargs.pop('hatch_colors', None)
    labels = kwargs.pop('labels', None)

    polycollections = ax.stackplot(x, *args, **kwargs)
    ylim = ax.get_ylim()
    ax.set_ylim((0, ylim[1]))
    patches = [mpl.patches.Rectangle((0,0), 1, 1) for pc in polycollections]
    
    if hatches is not None:
        hatch_cycle = itertools.cycle(hatches)

        for pc in polycollections:
            pc.set_hatch(hatch_cycle.next())
            pc.set_linewidth(0)            

    if hatch_colors is not None:
        color_cycle = itertools.cycle(hatch_colors)

        for pc in polycollections:
            pc.set_edgecolor(color_cycle.next())

        def get_patch(poly):
            patch = mpl.patches.Rectangle((0,0), 1, 1)
            patch.set_edgecolor(poly.get_edgecolor()[0])
            patch.set_facecolor(poly.get_facecolor()[0])
            patch.set_linewidth(poly.get_linewidth()[0])
            patch.set_hatch(poly.get_hatch())

            return patch

    if labels is None:
        labels = [str(i) for i in range(len(patches))]
    labels = reversed(labels)

    leg = ax.legend(
        map(get_patch, reversed(polycollections)),
        labels,
        bbox_to_anchor=(1.05, 1),
        loc=2)

    return leg



def save_duration_fig(df, path, title=None):

    time_res = NUM_HOURS / len(df.index)

    fig, ax = plt.subplots(1, 1)
    fig.set_size_inches((10/2.5, 9/2.5))

    df = df / time_res

    markers = [None, 'o', 's', 'x', 'v', '^', '>', '<']
    marker_cycle = itertools.cycle(markers)
    for col in df:
        hist, loads = np.histogram(df[col].values, bins=100, density=False)
        duration_above_loads = 100 * (1 - np.cumsum(hist)/len(df.index))
        ax.plot(
            duration_above_loads,
            loads[0:-1],
            label=col,
            marker=marker_cycle.next(),
            markevery=20)

    ax.set_xlabel('Duration [%]')
    ax.set_ylabel('Load [MW]')

    box = ax.get_position()    
    ax.set_ylim((0, ax.get_ylim()[1]))
    #ax.set_position([box.x0, box.y0, box.width * 0.6, box.height])
    leg = ax.legend(bbox_to_anchor=(1.05, 1), loc=2)

    suptitle = None
    if title is not None:
        suptitle = fig.suptitle(title)

    if suptitle is not None:
        extra_artists=(leg, suptitle)
    else:
        extra_artists=(leg,)

    fig.savefig(path, bbox_extra_artists=extra_artists, bbox_inches='tight')

    plt.close(fig)


def save_barplot_fig(series, path, xerr=None, title=None):
    fig, ax = plt.subplots(1, 1)

    fig.set_size_inches((10/2.5, 10/2.5))

    ypositions = np.arange(len(series)) + 0.5
    ax.barh(
        ypositions,
        series.values,
        xerr=xerr,
        linewidth=0)

    horz_offset = 0.03 * series.max()
    for pos, l, v in zip(ypositions, series.index.values, series.values):
        ax.annotate(
            str(int(np.round(v))),
            xy=(v - horz_offset, pos + .4),
            va='center',
            ha='right')

        ax.annotate(l,
            xy=(-5, pos + .4),
            va='center',
            ha='right')
    
    ax.set_yticks(ypositions + 0.4)
    ax.set_yticklabels(series.index.values)

    ax.get_yaxis().grid(b=False)
    for l in ax.get_yaxis().get_ticklines():
        l.set_visible(False)

    if title is not None:
        fig.suptitle(title)

    fig.savefig(path, bbox_inches='tight')

    plt.close(fig)

