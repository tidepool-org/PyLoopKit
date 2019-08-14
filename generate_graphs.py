#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 13:11:40 2019

@author: annaquinlan, plot style from Ed Nykaza
"""
from collections import OrderedDict
import matplotlib.pyplot as plt
from date import time_interval_since


def plot_graph(
        dates, values,
        x_label=None, y_label=None, title=None,
        line_color=None, fill_color=None, file_name=None, grid=False,
        line_style="-", scatter=False):
    relative_dates = []

    # convert from exact dates to relative dates
    for i in range(0, len(dates)):
        date = dates[i]
        hours = date.hour + date.minute / 60 + date.second / 3600

        # adjust if the times cross midnight
        if (len(relative_dates) > 0
                and relative_dates[i-1] > hours):
            hours += 24
        relative_dates.append(hours)

    font = {
        'family': 'DejaVu Sans',
        'weight': 'bold',
        'size': 15
    }
    plt.rc('font', **font)

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

    # if we cross midnight, adjust so the graph displays correctly
    if not sorted(x_ticks) == x_ticks:
        for i in range(1, len(x_ticks)):
            if x_ticks[i-1] > x_ticks[i]:
                x_ticks[i] = x_ticks[i] + 24

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
    plt.show()


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

    font = {
        'family': 'DejaVu Sans',
        'weight': 'bold',
        'size': 15
    }
    plt.rc('font', **font)

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
    plt.show()


def plot_multiple_relative_graphs(
        dates, values,
        x_label=None, y_label=None, title=None,
        line_color=None, fill_color=None, file_name=None, grid=False,
        ls_list=None):

    assert len(dates) == len(values)

    font = {
        'family': 'DejaVu Sans',
        'weight': 'bold',
        'size': 15
    }
    plt.rc('font', **font)

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
    plt.show()


def plot_loop_inspired_glucose_graph(
        overall_dates, overall_values,
        momentum_dates=None, momentum_values=None,
        insulin_dates=None, insulin_values=None,
        carb_dates=None, carb_values=None,
        retrospective_dates=None, retrospective_values=None,
        x_label=None, y_label=None, title=None,
        previous_glucose_dates=None, previous_glucose_values=None,
        line_color=None, file_name=None, grid=False,
        line_style="-", target_min=90, target_max=120):
    """ Create a Loop-inspired graph. Limitation: can only do one correction
        range.
    """
    def plot_line(
            absolute_dates, values,
            line_color="#5ac6fa",
            style="--",
            thickness=4,
            label=None):
        relative_dates = []
        for i in range(0, len(absolute_dates)):
            date = absolute_dates[i]
            hours = date.hour + date.minute / 60 + date.second / 3600

            # adjust if the times cross midnight
            if (len(relative_dates) > 0
                    and relative_dates[i-1] > hours):
                hours += 24
            relative_dates.append(hours)

        ax.plot(
            relative_dates, values, color=line_color,
            ls=style, lw=thickness, label=label
        )

    font = {
        'family': 'DejaVu Sans',
        'weight': 'bold',
        'size': 15
    }
    plt.rc('font', **font)

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

    if previous_glucose_dates:
        x_ticks_duplicates = [
            date.hour for date in previous_glucose_dates
            ] + [date.hour for date in overall_dates]

    else:
        x_ticks_duplicates = [date.hour for date in overall_dates]

    x_ticks = list(OrderedDict.fromkeys(x_ticks_duplicates))
    labels = ["%d:00" % x1 for x1 in x_ticks]

    # if the times cross midnight, adjust
    if not sorted(x_ticks) == x_ticks:
        for i in range(1, len(x_ticks)):
            if x_ticks[i-1] > x_ticks[i]:
                x_ticks[i] = x_ticks[i] + 24

    plt.xticks(x_ticks, labels)

    # find the correct length to fill the correction range
    fill_length = [
        x_ticks[0],
        x_ticks[-1] if x_ticks[0] != x_ticks[-1] else x_ticks[0] + 1
    ]

    # plot correction range
    if abs(target_min - target_min) > 0:
        ax.fill_between(
            fill_length,
            [target_min, target_min],
            [target_max, target_max],
            facecolor='#B5E7FF',
            lw=0
        )
        plt.plot(
            [], [],
            color='#B5E7FF',
            lw=10,
            label="Target Range: %d-%d" % (target_min, target_max)
        )
    else:
        plt.axhline(
            y=target_min,
            color='#B5E7FF',
            lw=3,
            label="Target Range: %d-%d" % (target_min, target_max)
        )

    # set labels and title
    if x_label:
        ax.set_xlabel(x_label)
    if y_label:
        ax.set_ylabel(y_label)
    if title:
        plt.title(title, loc="left", fontweight='bold')

    scatter_dates = []
    line_dates = []

    # convert from exact dates to relative dates, adjusting for date changes
    if previous_glucose_dates:
        for i in range(0, len(previous_glucose_dates)):
            date = previous_glucose_dates[i]
            hours = date.hour + date.minute / 60 + date.second / 3600

            # adjust if the times cross midnight
            if (len(scatter_dates) > 0
                    and scatter_dates[i-1] > hours):
                hours += 24
            scatter_dates.append(hours)

    for i in range(0, len(overall_dates)):
        date = overall_dates[i]
        hours = date.hour + date.minute / 60 + date.second / 3600

        # adjust if the times cross midnight
        if (len(line_dates) > 0
                and line_dates[i-1] > hours):
            hours += 24
        line_dates.append(hours)

    if previous_glucose_dates:
        ax.scatter(
            scatter_dates, previous_glucose_values,
            color=line_color or "#5ac6fa", lw=4, ls="-", s=10
        )

    # Plot the overall prediction line
    plot_line(
        overall_dates, overall_values,
        label="Predicted Glucose (Overall)"
    )

    # Plot each individual effect, if it exists
    if momentum_dates:
        plot_line(
            momentum_dates, momentum_values,
            line_color="#eb5905", thickness=3,
            label="Predicted Glucose (Momentum Only)"
        )
    if insulin_dates:
        plot_line(
            insulin_dates, insulin_values,
            line_color="#f29741", thickness=3,
            label="Predicted Glucose (Insulin Only)"
        )
    if carb_dates:
        plot_line(
            carb_dates, carb_values,
            line_color="#5FCB49", thickness=3,
            label="Predicted Glucose (Carb Only)"
        )
    if retrospective_dates:
        plot_line(
            retrospective_dates, retrospective_values,
            line_color="#4253ed", thickness=3,
            label="Predicted Glucose (RC Only)"
        )

    # add a legend
    leg = plt.legend(numpoints=1)
    for text in leg.get_texts():
        text.set_color('#606060')
        text.set_weight('normal')

    # add a grid
    plt.grid(grid)
    # save the output graph
    if file_name:
        plt.savefig(file_name + ".png")

    plt.show()
