#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 13:11:40 2019

@author: annaquinlan, plot style from Ed Nykaza
"""
from collections import OrderedDict
from datetime import timedelta, datetime
import matplotlib.pyplot as plt
from matplotlib import collections as mc

from pyloopkit.date import time_interval_since
from pyloopkit.insulin_math import schedule_offset


def plot_graph(
        dates, values,
        x_label=None, y_label=None, title=None,
        line_color=None, fill_color=None,
        file_name=None, grid=False,
        line_style="-", scatter=False):
    """ Plot an Loop-style effects graph, with the x-axis ticks
        being absolute hour of the day (ex: 13:00)

    dates -- datetimes of dates to plot at
    values -- integer values to plot
    Optional parameters:
        x_label -- the x-axis label
        y_label -- the y-axis label
        title -- the title of the graph
        line_color -- color of the line that is graphed
        fill_color -- the color of the fill under the graph (defaults to
                      no fill)
        file_name -- name to save the plot as (if no name is specified, the
                     graph is not saved)
        grid -- set to True to enable a grid on the graph
        line_style -- see pyplot documentation for the line style options
        scatter -- plot points as a scatter plot instead of a line
    """
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
    """ Plot an Loop-style effects graph, with the x-axis ticks
        being the relative time since the first value (ex: 4 hours)

    dates -- datetimes of dates to plot at
    values -- integer values to plot

    Optional parameters:
        x_label -- the x-axis label
        y_label -- the y-axis label
        title -- the title of the graph
        line_color -- color of the line that is graphed
        fill_color -- the color of the fill under the graph (defaults to
                      no fill)
        file_name -- name to save the plot as (if no name is specified, the
                     graph is not saved)
        grid -- set to True to enable a grid on the graph
        line_style -- see pyplot documentation for the line style options
        scatter -- plot points as a scatter plot instead of a line
    """
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
        line_color=None, fill_color=None, file_name=None, grid=False):
    """ Plot an Loop-style effects graph, with the x-axis ticks
        being the relative time since the first value (ex: 4 hours) AND there
        being multiple lines on the same graph

    dates -- lists of dates to plot at (datetime)
        ex: [
                [1:00, 2:00],
                [1:00, 2:00]
            ]
    values -- lists of integer values to plot
        ex: ex: [
                [2, 4],
                [0, -20]
            ]

    Optional parameters:
        x_label -- the x-axis label
        y_label -- the y-axis label
        title -- the title of the graph
        line_color -- color of the line that is graphed
        fill_color -- the color of the fill under the graph (defaults to
                      no fill)
        file_name -- name to save the plot as (if no name is specified, the
                     graph is not saved)
        grid -- set to True to enable a grid on the graph
        line_style -- see pyplot documentation for the line style options
        scatter -- plot points as a scatter plot instead of a line
    """
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
        previous_glucose_dates=None, previous_glucose_values=None,
        x_label=None, y_label=None, title=None,
        line_color=None, file_name=None, grid=False,
        line_style="-", target_min=None, target_max=None,
        correction_range_starts=None, correction_range_ends=None,
        correction_range_mins=None, correction_range_maxes=None):
    """ Create a Loop-inspired prediction line graph.

    overall_dates -- dates of overall prediction
    overall_values -- BG values of overall prediction

    momentum_dates, insulin_dates, carb_dates, retrospective_dates - dates
        of BG prediction that includes only the named effect
    momentum_values, insulin_values, carb_values, retrospective_values - values
        of BG prediction that includes only the named effect

    previous_glucose_dates -- dates of previous CGM points
    previous_glucose_values -- values of previous CGM points

    Optional parameters:
        x_label -- the x-axis label
        y_label -- the y-axis label
        title -- the title of the graph
        line_color -- color of the line that is graphed
        fill_color -- the color of the fill under the graph (defaults to
                      no fill)
        file_name -- name to save the plot as (if no name is specified, the
                     graph is not saved)
        grid -- set to True to enable a grid on the graph
        line_style -- see pyplot documentation for the line style options

        target_min -- the minimum correction range target for the whole
                      duration of the prediction
        target_max -- the maximum correction range target for the whole
                      duration of the prediction

        * passing these will override the target_min and target_max *
        correction_range_starts -- start times for target ranges (datetime)
        correction_range_ends -- stop times for given target ranges (datetime)
        correction_range_mins -- the lower bounds of target ranges (mg/dL)
        correction_range_maxes -- the upper bounds of target ranges (mg/dL)
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

    # if there is a specified target range, it's assumed it will be for the
    # whole duration of the graph
    if target_min and target_max:
        # find the correct length to fill the correction range
        fill_length = [
            x_ticks[0],
            x_ticks[-1] if x_ticks[0] != x_ticks[-1] else x_ticks[0] + 1
        ]

        # plot correction range
        if abs(target_max - target_min) > 0:
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

    elif correction_range_starts:
        start = min(
            previous_glucose_dates[0] or overall_dates[0],
            overall_dates[0]
        )
        end = max(
            start + timedelta(hours=1),
            overall_dates[-1]
        )
        (range_starts,
         range_ends,
         range_mins,
         range_maxes
         ) = correction_ranges_between(
             correction_range_starts,
             correction_range_ends,
             correction_range_mins,
             correction_range_maxes,
             start,
             end
             )

        for i in range(0, len(range_starts)):
            # find the fill length, adjusting if the dates cross midnight
            fill_start = x_ticks[0] if i == 0 else (
                range_starts[i].hour if range_starts[i].day == start.day
                else range_starts[i].hour + 24
            )
            fill_end = x_ticks[-1] if i == len(range_starts) - 1 else (
                range_ends[i].hour if range_ends[i].day == start.day
                else range_ends[i].hour + 24
            )
            fill_length = (
                fill_start,
                fill_end
            )
            # plot the range
            if abs(range_mins[i] - range_maxes[i]) > 0:
                ax.fill_between(
                    fill_length,
                    [range_mins[i], range_mins[i]],
                    [range_maxes[i], range_maxes[i]],
                    facecolor='#B5E7FF',
                    lw=0
                )
                plt.plot(
                    [], [],
                    color='#B5E7FF',
                    lw=10,
                    label="Target Range"
                )
            else:
                line = [
                    [
                        (fill_length[0], range_mins[i]),
                        (fill_length[1], range_mins[i])
                    ]
                ]
                lc = mc.LineCollection(line, colors='#B5E7FF', linewidths=3)
                ax.add_collection(lc)

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
            color=line_color or "#5ac6fa",
            lw=4,
            ls="-",
            s=10,
            label="CGM Data"
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
            line_color="#eb5905", thickness=5,
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

    # display the eventual BG
    ax.text(
        max(ax.get_xlim()),
        max(ax.get_ylim()) + 4,
        "Eventually %d mg/dL" % overall_values[-1],
        horizontalalignment="right",
        size=15,
        color="#a6a5a2"
    )

    plt.show()


def correction_ranges_between(
        correction_range_starts, correction_range_ends,
        correction_range_mins, correction_range_maxes,
        start_date, end_date,
        repeat_interval=24
    ):
    """ Returns a slice of scheduled basal rates that occur between two dates

    Arguments:
    basal_start_times -- list of times the basal rates start at
    basal_rates -- list of basal rates(U/hr)
    basal_minutes -- list of basal lengths (in mins)
    start_date -- start date of the range (datetime obj)
    end_date -- end date of the range (datetime obj)
    repeat_interval -- the duration over which the rates repeat themselves
                       (24 hours by default)

    Output:
    Tuple in format (basal_start_times, basal_rates, basal_minutes) within
    the range of dose_start_date and dose_end_date
    """
    timezone_info = start_date.tzinfo
    if start_date > end_date:
        return ([], [], [])

    reference_time_interval = timedelta(
        hours=correction_range_starts[0].hour,
        minutes=correction_range_starts[0].minute,
        seconds=correction_range_starts[0].second
    )
    max_time_interval = (
        reference_time_interval
        + timedelta(hours=repeat_interval)
    )

    start_offset = schedule_offset(start_date, correction_range_starts[0])

    end_offset = (
        start_offset
        + timedelta(seconds=time_interval_since(end_date, start_date))
    )

    # if a dose is crosses days, split it into separate doses
    if end_offset > max_time_interval:
        boundary_date = start_date + (max_time_interval - start_offset)
        (start_times_1,
         end_times_1,
         mins_1,
         maxes_1,
         ) = correction_ranges_between(
             correction_range_starts,
             correction_range_ends,
             correction_range_mins,
             correction_range_maxes,
             start_date,
             boundary_date,
             repeat_interval=repeat_interval
             )
        (start_times_2,
         end_times_2,
         mins_2,
         maxes_2,
         ) = correction_ranges_between(
             correction_range_starts,
             correction_range_ends,
             correction_range_mins,
             correction_range_maxes,
             boundary_date,
             end_date,
             repeat_interval=repeat_interval
             )

        return (start_times_1 + start_times_2,
                end_times_1 + end_times_2,
                mins_1 + mins_2,
                maxes_1 + maxes_2
                )

    start_index = 0
    end_index = len(correction_range_starts)

    for (i, start_time) in enumerate(correction_range_starts):
        start_time = timedelta(
            hours=start_time.hour,
            minutes=start_time.minute,
            seconds=start_time.second
        )
        if start_offset >= start_time:
            start_index = i
        if end_offset < start_time:
            end_index = i
            break

    reference_date = start_date - start_offset
    reference_date = datetime(
        year=reference_date.year,
        month=reference_date.month,
        day=reference_date.day,
        hour=reference_date.hour,
        minute=reference_date.minute,
        second=reference_date.second,
        tzinfo=timezone_info
        )

    if start_index > end_index:
        return ([], [], [])

    (output_start_times,
     output_end_times,
     output_mins,
     output_maxes
     ) = ([], [], [], [])

    for i in range(start_index, end_index):
        end_time = (timedelta(
            hours=correction_range_starts[i+1].hour,
            minutes=correction_range_starts[i+1].minute,
            seconds=correction_range_starts[i+1].second) if i+1 <
                    len(correction_range_starts) else max_time_interval)

        output_start_times.append(
            reference_date + timedelta(
                hours=correction_range_starts[i].hour,
                minutes=correction_range_starts[i].minute,
                seconds=correction_range_starts[i].second
            )
        )
        output_end_times.append(reference_date + end_time)
        output_mins.append(correction_range_mins[i])
        output_maxes.append(correction_range_maxes[i])

    assert len(output_start_times) == len(output_end_times) ==\
        len(output_mins) == len(output_maxes),\
        "expected output shape to match"

    return (output_start_times, output_end_times, output_mins, output_maxes)
