#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 11 13:03:07 2019

@author: annaquinlan
"""
import json
import datetime

from generate_graphs import plot_graph, plot_loop_inspired_glucose_graph
from insulin_math import find_ratio_at_time
from loop_kit_tests import find_root_path
from loop_math import predict_glucose
from pyloop_parser import parse_report_and_run

# find the path to the file in the repo
name = "example_issue_report.json"
path = find_root_path(name.split(".")[0], "." + name.split(".")[1])

# run the Loop algorithm with the issue report data
recommendations = parse_report_and_run(path, name)

# generate separate glucose predictions using each effect individually
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

inputs = recommendations.get("input_data")

plot_loop_inspired_glucose_graph(
    recommendations.get("predicted_glucose_dates"),
    recommendations.get("predicted_glucose_values"),
    title="Predicted Glucose",
    line_color="#5ac6fa",
    grid=True,
    previous_glucose_dates=inputs.get("glucose_dates")[-15:],
    previous_glucose_values=inputs.get("glucose_values")[-15:],
    target_min=find_ratio_at_time(
        inputs.get("target_range_start_times"),
        inputs.get("target_range_end_times"),
        inputs.get("target_range_minimum_values"),
        inputs.get("time_to_calculate_at")
        ),
    target_max=find_ratio_at_time(
        inputs.get("target_range_start_times"),
        inputs.get("target_range_end_times"),
        inputs.get("target_range_maximum_values"),
        inputs.get("time_to_calculate_at")
        )
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
    target_min=find_ratio_at_time(
        inputs.get("target_range_start_times"),
        inputs.get("target_range_end_times"),
        inputs.get("target_range_minimum_values"),
        inputs.get("time_to_calculate_at")
        ),
    target_max=find_ratio_at_time(
        inputs.get("target_range_start_times"),
        inputs.get("target_range_end_times"),
        inputs.get("target_range_maximum_values"),
        inputs.get("time_to_calculate_at")
        )
    )
