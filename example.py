#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 11 13:03:07 2019

@author: annaquinlan
"""
# pylint: disable=C0103
import json
import datetime
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot

from pyloopkit.dose import DoseType
from pyloopkit.generate_graphs import plot_graph, plot_loop_inspired_glucose_graph
#from .loop_kit_tests import find_root_path
from pyloopkit.loop_math import predict_glucose
from pyloopkit.pyloop_parser import (
    parse_report_and_run, parse_dictionary_from_previous_run
)

# %% find the path to the file in the repo
# uncomment the name of the file you'd like to run
name = "example_issue_report_1.json"
# name = "example_issue_report_2.json"
# name = "example_issue_report_3.json"
# name = "example_from_previous_run.json"

path = "pyloopkit/example_files/"

# run the Loop algorithm with the issue report data

# uncomment parse_report_and_run if using an issue report; uncomment
# parse_dictionary_from_previous_run if using data from a previous run
recommendations = parse_report_and_run(path, name)
# recommendations = parse_dictionary_from_previous_run(path, name)

# %% generate separate glucose predictions using each effect individually
starting_date = recommendations.get("input_data").get("glucose_dates")[-1]
starting_glucose = recommendations.get("input_data").get("glucose_values")[-1]

(momentum_predicted_glucose_dates,
 momentum_predicted_glucose_values
 ) = predict_glucose(
     starting_date, starting_glucose,
     momentum_dates=recommendations.get("momentum_effect_dates"),
     momentum_values=recommendations.get("momentum_effect_values")
     )

(insulin_predicted_glucose_dates,
 insulin_predicted_glucose_values
 ) = predict_glucose(
     starting_date, starting_glucose,
     insulin_effect_dates=recommendations.get("insulin_effect_dates"),
     insulin_effect_values=recommendations.get("insulin_effect_values")
     )

(carb_predicted_glucose_dates,
 carb_predicted_glucose_values
 ) = predict_glucose(
     starting_date, starting_glucose,
     carb_effect_dates=recommendations.get("carb_effect_dates"),
     carb_effect_values=recommendations.get("carb_effect_values")
     )

if recommendations.get("retrospective_effect_dates"):
    (retrospective_predicted_glucose_dates,
     retrospective_predicted_glucose_values
     ) = predict_glucose(
         starting_date, starting_glucose,
         correction_effect_dates=recommendations.get(
             "retrospective_effect_dates"
         ),
         correction_effect_values=recommendations.get(
             "retrospective_effect_values"
         )
         )
else:
    (retrospective_predicted_glucose_dates,
     retrospective_predicted_glucose_values
     ) = ([], [])


# save dictionary as json file
def convert_times_and_types(obj):
    """ Convert dates and dose types into strings when saving as a json """
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, datetime.time):
        return obj.isoformat()
    if isinstance(obj, DoseType):
        return str(obj.name)


with open(name.split(".")[0] + "-output.json", "w") as f:
    json.dump(
        recommendations,
        f,
        sort_keys=True,
        indent=4,
        default=convert_times_and_types
    )

# %% Visualize output effect data

# plot insulin effects
plot_graph(
    recommendations.get("insulin_effect_dates"),
    recommendations.get("insulin_effect_values"),
    title="Insulin Effect",
    grid=True,
    )

# plot counteraction effects
plot_graph(
    recommendations.get("counteraction_effect_start_times")[
        # trim to a reasonable length so the effects aren't too close together
        -len(recommendations.get("insulin_effect_dates")):
    ],
    recommendations.get("counteraction_effect_values")[
        # trim to a reasonable length so the effects aren't too close together
        -len(recommendations.get("insulin_effect_dates")):
    ],
    title="Counteraction Effects",
    fill_color="#f09a37",
    grid=True
    )

# only plot carb effects if we have that data
if recommendations.get("carb_effect_values"):
    plot_graph(
        recommendations.get("carb_effect_dates"),
        recommendations.get("carb_effect_values"),
        title="Carb Effect",
        line_color="#5FCB49",
        grid=True
        )

# only plot the carbs on board over time if we have that data
if recommendations.get("cob_timeline_values"):
    plot_graph(
        recommendations.get("cob_timeline_dates"),
        recommendations.get("cob_timeline_values"),
        title="Carbs on Board",
        line_color="#5FCB49", fill_color="#63ed47"
        )

# %% Visualize output data as a Loop-style plot
inputs = recommendations.get("input_data")

plot_loop_inspired_glucose_graph(
    recommendations.get("predicted_glucose_dates"),
    recommendations.get("predicted_glucose_values"),
    title="Predicted Glucose",
    line_color="#5ac6fa",
    grid=True,
    previous_glucose_dates=inputs.get("glucose_dates")[-15:],
    previous_glucose_values=inputs.get("glucose_values")[-15:],
    correction_range_starts=inputs.get("target_range_start_times"),
    correction_range_ends=inputs.get("target_range_end_times"),
    correction_range_mins=inputs.get("target_range_minimum_values"),
    correction_range_maxes=inputs.get("target_range_maximum_values")
    )


plot_loop_inspired_glucose_graph(
    recommendations.get("predicted_glucose_dates"),
    recommendations.get("predicted_glucose_values"),
    momentum_predicted_glucose_dates,
    momentum_predicted_glucose_values,
    insulin_predicted_glucose_dates,
    insulin_predicted_glucose_values,
    carb_predicted_glucose_dates,
    carb_predicted_glucose_values,
    retrospective_predicted_glucose_dates,
    retrospective_predicted_glucose_values,
    title="Predicted Glucose",
    line_color="#5ac6fa",
    grid=True,
    previous_glucose_dates=inputs.get("glucose_dates")[-15:],
    previous_glucose_values=inputs.get("glucose_values")[-15:],
    correction_range_starts=inputs.get("target_range_start_times"),
    correction_range_ends=inputs.get("target_range_end_times"),
    correction_range_mins=inputs.get("target_range_minimum_values"),
    correction_range_maxes=inputs.get("target_range_maximum_values")
    )

# %% visualize inputs as a Tidepool daily view
current_time = inputs.get("time_to_calculate_at")

# blood glucose data
glucose_dates = pd.DataFrame(inputs.get("glucose_dates"), columns=["time"])
glucose_values = pd.DataFrame(inputs.get("glucose_values"), columns=["mg_dL"])
bg = pd.concat([glucose_dates, glucose_values], axis=1)

# Set bg color values
bg['bg_colors'] = 'mediumaquamarine'
bg.loc[bg['mg_dL'] < 54, 'bg_colors'] = 'indianred'
low_location = (bg['mg_dL'] > 54) & (bg['mg_dL'] < 70)
bg.loc[low_location, 'bg_colors'] = 'lightcoral'
high_location = (bg['mg_dL'] > 180) & (bg['mg_dL'] <= 250)
bg.loc[high_location, 'bg_colors'] = 'mediumpurple'
bg.loc[(bg['mg_dL'] > 250), 'bg_colors'] = 'slateblue'

bg_trace = go.Scattergl(
    name="bg",
    x=bg["time"],
    y=bg["mg_dL"],
    hoverinfo="y+name",
    mode='markers',
    marker=dict(
        size=6,
        line=dict(width=0),
        color=bg["bg_colors"]
    )
)

# bolus data
dose_start_times = (
    pd.DataFrame(inputs.get("dose_start_times"), columns=["startTime"])
)
dose_end_times = (
    pd.DataFrame(inputs.get("dose_end_times"), columns=["endTime"])
)
dose_values = (
    pd.DataFrame(inputs.get("dose_values"), columns=["dose"])
)
dose_types = (
    pd.DataFrame(inputs.get("dose_types"), columns=["type"])
)

dose_types["type"] = dose_types["type"].apply(convert_times_and_types)

dose = pd.concat(
    [dose_start_times, dose_end_times, dose_values, dose_types],
    axis=1
)

unique_dose_types = dose["type"].unique()

# bolus data
if "bolus" in unique_dose_types:
    bolus = dose[dose["type"] == "bolus"]
    bolus_trace = go.Bar(
        name="bolus",
        x=bolus["startTime"],
        y=bolus["dose"],
        hoverinfo="y+name",
        width=999999,
        marker=dict(color='lightskyblue')
    )

# basals rates
# scheduled basal rate
basal_rate_start_times = (
    pd.DataFrame(inputs.get("basal_rate_start_times"), columns=["time"])
)
basal_rate_minutes = (
    pd.DataFrame(inputs.get("basal_rate_minutes"), columns=["duration"])
)
basal_rate_values = (
    pd.DataFrame(inputs.get("basal_rate_values"), columns=["sbr"])
)
sbr = pd.concat(
    [basal_rate_start_times, basal_rate_minutes, basal_rate_values],
    axis=1
)

# create a contiguous basal time series
bg_range = pd.date_range(
    bg["time"].min() - datetime.timedelta(days=1),
    current_time,
    freq="1s"
)
contig_ts = pd.DataFrame(bg_range, columns=["datetime"])
contig_ts["time"] = contig_ts["datetime"].dt.time
basal = pd.merge(contig_ts, sbr, on="time", how="left")
basal["sbr"].fillna(method='ffill', inplace=True)
basal.dropna(subset=['sbr'], inplace=True)

# temp basal data
if ("basal" in unique_dose_types) | ("suspend" in unique_dose_types):
    temp_basal = (
        dose[((dose["type"] == "basal") | (dose["type"] == "suspend"))]
    )

    temp_basal["type"].replace("basal", "temp", inplace=True)
    all_temps = pd.DataFrame()
    for idx in temp_basal.index:
        rng = pd.date_range(
            temp_basal.loc[idx, "startTime"],
            temp_basal.loc[idx, "endTime"] - datetime.timedelta(seconds=1),
            freq="1s"
        )
        temp_ts = pd.DataFrame(rng, columns=["datetime"])
        temp_ts["tbr"] = temp_basal.loc[idx, "dose"]
        temp_ts["type"] = temp_basal.loc[idx, "type"]
        all_temps = pd.concat([all_temps, temp_ts])

    basal = pd.merge(basal, all_temps, on="datetime", how="left")
    basal["type"].fillna("scheduled", inplace=True)

else:
    basal["tbr"] = np.nan

basal["delivered"] = basal["tbr"]
basal.loc[basal["delivered"].isnull(), "delivered"] = (
    basal.loc[basal["delivered"].isnull(), "sbr"]
)

sbr_trace = go.Scatter(
    name="scheduled",
    mode='lines',
    x=basal["datetime"],
    y=basal["sbr"],
    hoverinfo="y+name",
    showlegend=False,
    line=dict(
        shape='vh',
        color='cornflowerblue',
        dash='dot'
    )
)

basal_trace = go.Scatter(
    name="delivered",
    mode='lines',
    x=basal["datetime"],
    y=basal["delivered"],
    hoverinfo="y+name",
    showlegend=False,
    line=dict(
        shape='vh',
        color='cornflowerblue'
    ),
    fill='tonexty'
)

# carb data
# carb-to-insulin-ratio
carb_ratio_start_times = (
    pd.DataFrame(inputs.get("carb_ratio_start_times"), columns=["time"])
)
carb_ratio_values = (
    pd.DataFrame(inputs.get("carb_ratio_values"), columns=["cir"])
)
cir = pd.concat([carb_ratio_start_times, carb_ratio_values], axis=1)

carbs = pd.merge(contig_ts, cir, on="time", how="left")
carbs["cir"].fillna(method='ffill', inplace=True)
carbs.dropna(subset=['cir'], inplace=True)

# carb events
carb_dates = pd.DataFrame(inputs.get("carb_dates"), columns=["datetime"])
carb_values = pd.DataFrame(inputs.get("carb_values"), columns=["grams"])
carb_absorption_times = (
    pd.DataFrame(
        inputs.get("carb_absorption_times"),
        columns=["aborption_time"]
    )
)
carb_events = (
    pd.concat([carb_dates, carb_values, carb_absorption_times], axis=1)
)

carbs = pd.merge(carbs, carb_events, on="datetime", how="left")

# add bolus height for figure
carbs["bolus_height"] = carbs["grams"] / carbs["cir"]

carb_trace = go.Scatter(
    name="carbs",
    mode='markers + text',
    x=carbs["datetime"],
    y=carbs["bolus_height"] + 2,
    hoverinfo="name",
    marker=dict(
        color='gold',
        size=25
    ),
    showlegend=False,
    text=carbs["grams"],
    textposition='middle center'
)

# combine the plots
basal_trace.yaxis = "y"
sbr_trace.yaxis = "y"
bolus_trace.yaxis = "y2"
carb_trace.yaxis = "y2"
bg_trace.yaxis = "y3"

data = [basal_trace, sbr_trace, bolus_trace, carb_trace, bg_trace]
layout = go.Layout(
    yaxis=dict(
        domain=[0, 0.2],
        range=[0, max(basal["sbr"].max(), basal["tbr"].max()) + 1],
        fixedrange=True,
        hoverformat=".2f",
        title=dict(
            text="Basal Rate U/hr",
            font=dict(
                size=12
            )
        )
    ),
    showlegend=False,
    yaxis2=dict(
        domain=[0.25, 0.45],
        range=[0, max(bolus["dose"].max(), carbs["bolus_height"].max()) + 10],
        fixedrange=True,
        hoverformat=".1f",
        title=dict(
            text="Bolus U",
            font=dict(
                size=12
            )
        )
    ),
    yaxis3=dict(
        domain=[0.5, 1],
        range=[0, 402],
        fixedrange=True,
        hoverformat=".0f",
        title=dict(
            text="Blood Glucose mg/dL",
            font=dict(
                size=12
            )
        )
    ),
    xaxis=dict(
        range=(
            current_time - datetime.timedelta(days=1),
            current_time + datetime.timedelta(minutes=60)
        )
    ),
    dragmode="pan",
)

fig = go.Figure(data=data, layout=layout)
plot(fig, filename=name.split(".")[0] + '-output.html')
