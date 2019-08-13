#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 11 15:56:36 2019

@author: annaquinlan
"""
from datetime import datetime, time
from collections import OrderedDict
import matplotlib.pyplot as plt

from date import time_interval_since
from generate_graphs import plot_relative_graph
from insulin_math import glucose_effects, insulin_on_board


def cumulative_insulin_effect_graph(save=False):
    (effect_dates,
     effect_values
     ) = glucose_effects(
         ["bolus"],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [2],
         [0],
         [360, 75],
         [time(0, 0)],
         [time(0, 0)],
         [50]
         )

    plot_relative_graph(
        effect_dates,
        effect_values,
        title="Cumulative Insulin Effect on Blood Glucose (mg/dL)",
        file_name="insulin_effect_for_alg_doc" if save else None,
        x_label="Time Since Delivery (Hours)",
        grid=True
        )


def insulin_on_board_percentage_graph(save=False):
    (iob_dates,
     iob_values
     ) = insulin_on_board(
         ["bolus"],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [2],
         [0],
         [360, 75]
         )
    percentages = [
        value / iob_values[0] * 100
        for value in iob_values
    ]

    plot_relative_graph(
        iob_dates,
        percentages,
        title="Insulin-On-Board (%)",
        file_name="iob_percent_timeline_for_alg_doc" if save else None,
        x_label="Time Since Delivery (Hours)",
        grid=True,
        fill_color="#f09a37"
        )


def insulin_on_board_graph(save=False):
    (iob_dates,
     iob_values
     ) = insulin_on_board(
         ["bolus"],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [2],
         [0],
         [360, 75]
         )

    plot_relative_graph(
        iob_dates,
        iob_values,
        title="Insulin-On-Board (U)",
        file_name="iob_timeline_for_alg_doc" if save else None,
        x_label="Time Since Delivery (Hours)",
        grid=True,
        fill_color="#f09a37"
        )


def insulin_absorption_graph(save=False):
    (effect_dates,
     effect_values
     ) = glucose_effects(
         ["bolus"],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [2],
         [0],
         [360, 75],
         [time(0, 0)],
         [time(0, 0)],
         [50]
         )

    isf = 50
    absorptions = []
    for i in range(1, len(effect_values)):
        absorptions.append(
            (effect_values[i-1] - effect_values[i]) * 12 / isf
        )

    plot_relative_graph(
        effect_dates[:-1],
        absorptions,
        title="Insulin Absorption (U/hr)",
        file_name="insulin_absorption_for_alg_doc" if save else None,
        x_label="Time Since Delivery (Hours)",
        grid=True
        )


def all_insulin_absorption_curves_graph(save=False):
    (adult_effect_dates,
     adult_effect_values
     ) = glucose_effects(
         ["bolus"],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [2],
         [0],
         [360, 65],
         [time(0, 0)],
         [time(0, 0)],
         [50]
         )
    isf = 50
    adult_relative_times = []
    adult_absorptions = []

    for i in range(1, len(adult_effect_values)):
        adult_relative_times.append(
            time_interval_since(
                adult_effect_dates[i-1], adult_effect_dates[0]
            ) / 3600
        )
        adult_absorptions.append(
            (adult_effect_values[i-1] - adult_effect_values[i]) * 12 / isf
        )

    (child_effect_dates,
     child_effect_values
     ) = glucose_effects(
         ["bolus"],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [2],
         [0],
         [360, 75],
         [time(0, 0)],
         [time(0, 0)],
         [50]
         )
    isf = 50
    child_relative_times = []
    child_absorptions = []

    for i in range(1, len(child_effect_values)):
        child_relative_times.append(
            time_interval_since(
                adult_effect_dates[i-1], adult_effect_dates[0]
            ) / 3600
        )
        child_absorptions.append(
            (child_effect_values[i-1] - child_effect_values[i]) * 12 / isf
        )

    (fiasp_effect_dates,
     fiasp_effect_values
     ) = glucose_effects(
         ["bolus"],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [2],
         [0],
         [360, 55],
         [time(0, 0)],
         [time(0, 0)],
         [50]
         )
    isf = 50
    fiasp_relative_times = []
    fiasp_absorptions = []

    for i in range(1, len(fiasp_effect_values)):
        fiasp_relative_times.append(
            time_interval_since(
                adult_effect_dates[i-1], adult_effect_dates[0]
            ) / 3600
        )
        fiasp_absorptions.append(
            (fiasp_effect_values[i-1] - fiasp_effect_values[i]) * 12 / isf
        )

    (walsh_effect_dates,
     walsh_effect_values
     ) = glucose_effects(
         ["bolus"],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [2],
         [0],
         [6],
         [time(0, 0)],
         [time(0, 0)],
         [50]
         )
    isf = 50
    walsh_relative_times = []
    walsh_absorptions = []

    for i in range(1, len(walsh_effect_values)):
        walsh_relative_times.append(
            time_interval_since(
                adult_effect_dates[i-1], adult_effect_dates[0]
            ) / 3600
        )
        walsh_absorptions.append(
            (walsh_effect_values[i-1] - walsh_effect_values[i]) * 12 / isf
        )
    # add the last absorption
    walsh_relative_times.append(walsh_relative_times[-1] + 5/60)
    walsh_absorptions.append(0)

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

    x_ticks_duplicates = [
        date.hour - walsh_effect_dates[0].hour for date in walsh_effect_dates
    ]
    x_ticks = list(OrderedDict.fromkeys(x_ticks_duplicates))
    labels = ["%d" % x1 for x1 in x_ticks]
    plt.xticks(x_ticks, labels)

    ax.set_xlabel("Time Since Delivery (Hours)")
    plt.title("Insulin Absorption (U/hr)", loc="left", fontweight='bold')

    ax.plot(
        adult_relative_times, adult_absorptions,
        color="#f09a37", lw=4, ls="-"
        )
    ax.plot(
        child_relative_times, child_absorptions,
        color="#f09a37", lw=4, ls=":"
        )
    ax.plot(
        fiasp_relative_times, fiasp_absorptions,
        color="#f09a37", lw=4, ls="--"
        )
    ax.plot(
        walsh_relative_times, walsh_absorptions,
        color="#f09a37", lw=4, ls="-."
        )

    plt.grid(True)
    leg = plt.legend(
             ["Rapid-Acting-Child (peak 65 min)",
              "Rapid-Acting-Adult (peak 75 min)",
              "Rapid-Acting-Fiasp (peak 55 min)",
              "Walsh-6hr-Model (peak 140 min)"
              ], edgecolor="black")
    for text in leg.get_texts():
        text.set_color("#606060")
        text.set_weight("normal")
    plt.savefig("insulin_absorption_curves_for_alg_doc" + ".png")


def insulin_effect_graph(save=False):
    (effect_dates,
     effect_values
     ) = glucose_effects(
         ["bolus"],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [2],
         [0],
         [360, 75],
         [time(0, 0)],
         [time(0, 0)],
         [50]
         )

    five_min_effects = []
    for i in range(1, len(effect_values)):
        five_min_effects.append(
            effect_values[i] - effect_values[i-1]
        )

    plot_relative_graph(
        effect_dates[:-1],
        five_min_effects,
        title="Change in Blood Glucose (mg/dL) Every 5 Minutes",
        file_name="5_min_insulin_effect_for_alg_doc" if save else None,
        x_label="Time Since Delivery (Hours)",
        grid=True,
        line_style=":",
        scatter=True
        )


def suspend_effect_graph(save=False):
    (effect_dates,
     effect_values
     ) = glucose_effects(
         ["suspend"],
         [datetime.fromisoformat("2019-08-08T00:00:00")],
         [datetime.fromisoformat("2019-08-08T01:00:00")],
         [0],
         [1],
         [360, 75],
         [time(0, 0)],
         [time(0, 0)],
         [50]
         )

    plot_relative_graph(
        effect_dates,
        effect_values,
        title="Cumulative BG Rise from a Temporary Basal of 0 U/hr for 1 hr with an ISF of 50",
        file_name="suspend_effect_for_alg_doc" if save else None,
        x_label="Time Since Delivery (Hours)",
        grid=True
        )
