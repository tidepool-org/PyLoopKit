#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 11 13:03:07 2019

@author: annaquinlan
"""
import json
import datetime

from generate_graphs import plot_graph
from loop_kit_tests import find_root_path
from pyloop_parser import parse_report_and_run

# find the path to the file in the repo
name = "high_bg_recommended_basal_and_bolus_report.json"
path = find_root_path(name.split(".")[0], "." + name.split(".")[1])

# run the Loop algorithm with the issue report data
recommendations = parse_report_and_run(path, name)


# save dictionary as json file
def convert_times(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, datetime.time):
        return obj.isoformat()


with open(name.split(".")[0] + "-output.json", "w") as f:
    json.dump(
        recommendations,
        f,
        sort_keys=True,
        indent=4,
        default=convert_times
    )

# visualize some of that data

plot_graph(
    recommendations.get("insulin_effect_dates"),
    recommendations.get("insulin_effect_values"),
    title="Insulin Effect",
    grid=True,
    )

plot_graph(
    recommendations.get("counteraction_effect_start_times")[-len(recommendations.get("insulin_effect_dates")):],
    recommendations.get("counteraction_effect_values")[-len(recommendations.get("insulin_effect_dates")):],
    title="Counteraction Effects",
    fill_color="#f09a37",
    grid=True
    )

plot_graph(
    recommendations.get("carb_effect_dates"),
    recommendations.get("carb_effect_values"),
    title="Carb Effect",
    line_color="#5FCB49",
    grid=True
    )

plot_graph(
    recommendations.get("cob_timeline_dates"),
    recommendations.get("cob_timeline_values"),
    title="Carbs on Board",
    line_color="#5FCB49", fill_color="#63ed47"
    )

plot_graph(
    recommendations.get("predicted_glucose_dates"),
    recommendations.get("predicted_glucose_values"),
    title="Predicted Glucose",
    line_color="#5ac6fa",
    grid=True
    )
