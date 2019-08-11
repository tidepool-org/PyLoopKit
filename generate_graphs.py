#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 13:11:40 2019

@author: annaquinlan, plot style from Ed Nykaza
"""
from collections import OrderedDict
import matplotlib.pyplot as plt


def plot_graph(
        dates, values,
        x_label=None, y_label=None, title=None,
        line_color=None, fill_color=None):
    relative_dates = []

    # convert from exact dates to relative dates
    for date in dates:
        relative_dates.append(
            date.hour + date.minute / 60 + date.second / 3600
        )

    figure_size_inches = (15, 7)
    fig, ax = plt.subplots(figsize=figure_size_inches)

    coord_color = "#c0c0c0"
    ax.spines['bottom'].set_color(coord_color)
    ax.spines['top'].set_color(coord_color)
    ax.spines['left'].set_color(coord_color)
    ax.spines['right'].set_color(coord_color)
    ax.xaxis.label.set_color(coord_color)
    ax.tick_params(axis='x', colors=coord_color)
    ax.yaxis.label.set_color(coord_color)
    ax.tick_params(axis='y', colors=coord_color)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)

    x_ticks_duplicates = [date.hour for date in dates]
    x_ticks = list(OrderedDict.fromkeys(x_ticks_duplicates))
    labels = ["%d:00" % x1 for x1 in x_ticks]
    plt.xticks(x_ticks, labels)

    if x_label:
        ax.set_xlabel(x_label)
    if y_label:
        ax.set_ylabel(y_label)
    if title:
        plt.title(title, loc="left", fontweight='bold')

    ax.plot(
        relative_dates, values, color=line_color or "#f09a37", lw=4, ls="-"
    )
    if fill_color:
        plt.fill_between(
            relative_dates, values, color=fill_color or "#f09a37", alpha=0.6
        )
