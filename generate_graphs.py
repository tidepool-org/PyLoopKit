#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 13:11:40 2019

@author: annaquinlan, plot style from Ed Nykaza
"""
import numpy as np
from matplotlib.ticker import AutoMinorLocator
from datetime import datetime
import matplotlib.ticker as mticker

from loop_kit_tests import load_fixture
from date import time_interval_since



from collections import OrderedDict
import matplotlib.pyplot as plt


def plot_graph(
        dates, values,
        x_label=None, y_label=None, title=None,
        line_color=None, fill_color=None, file_name=None, grid=False,
        line_style="-", scatter=False):
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

    if scatter:
        ax.scatter(
            relative_dates, values, color=line_color or "#f09a37"
        )
    else:
        ax.plot(
            relative_dates, values, color=line_color or "#f09a37", lw=4,
            ls=line_style
        )
    if fill_color:
        plt.fill_between(
            relative_dates, values, color=fill_color or "#f09a37", alpha=0.5
        )
    if grid:
        plt.grid(grid)
    if file_name:
        plt.savefig(file_name + ".png")


def plot_relative_graph(
        dates, values,
        x_label=None, y_label=None, title=None,
        line_color=None, fill_color=None, file_name=None, grid=False,
        line_style="-", scatter=False):
    relative_dates = []

    # convert from exact dates to relative dates
    for date in dates:
        relative_dates.append(
            time_interval_since(date, dates[0]) / 3600
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

    x_ticks_duplicates = [date.hour - dates[0].hour for date in dates]
    x_ticks = list(OrderedDict.fromkeys(x_ticks_duplicates))
    labels = ["%d" % x1 for x1 in x_ticks]
    plt.xticks(x_ticks, labels)

    if x_label:
        ax.set_xlabel(x_label)
    if y_label:
        ax.set_ylabel(y_label)
    if title:
        plt.title(title, loc="left", fontweight='bold')

    if scatter:
        ax.scatter(
            relative_dates, values, color=line_color or "#f09a37"
        )
    else:
        ax.plot(
            relative_dates, values, color=line_color or "#f09a37", lw=4,
            ls=line_style
        )
    if fill_color:
        plt.fill_between(
            relative_dates, values, color=fill_color or "#f09a37", alpha=0.5
        )
    if grid:
        plt.grid(grid)
    if file_name:
        plt.savefig(file_name + ".png")


def plot_multiple_relative_graphs(
        dates, values,
        x_label=None, y_label=None, title=None,
        line_color=None, fill_color=None, file_name=None, grid=False,
        ls_list=None):
    assert len(dates) == len(values)

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

    relative_dates = []
    # convert from exact dates to relative dates
    for date_list in dates:
        relative_date_list = []
        for date in date_list:
            relative_date_list.append(
                time_interval_since(date, date_list[0]) / 3600
            )
        relative_dates.append(relative_date_list)

    x_ticks_duplicates = [date.hour - dates[0][0].hour for date in dates[0]]
    x_ticks = list(OrderedDict.fromkeys(x_ticks_duplicates))
    labels = ["%d" % x1 for x1 in x_ticks]
    plt.xticks(x_ticks, labels)

    if x_label:
        ax.set_xlabel(x_label)
    if y_label:
        ax.set_ylabel(y_label)
    if title:
        plt.title(title, loc="left", fontweight='bold')

    for (date_list, value_list) in zip(dates, values):
        ax.plot(
            date_list, value_list, color=line_color or "#f09a37", lw=4, ls="-"
        )
    if fill_color:
        plt.fill_between(
            relative_dates, values, color=fill_color or "#f09a37", alpha=0.5
        )
    if grid:
        plt.grid(grid)
    if file_name:
        plt.savefig(file_name + ".png")
