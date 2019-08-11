#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 11 13:03:07 2019

@author: annaquinlan
"""
from generate_graphs import plot_graph
from loop_kit_tests import find_root_path
from pyloop_parser import parse_report_and_run

path = find_root_path("high_bg_recommended_basal_and_bolus_report", ".json")
name = "high_bg_recommended_basal_and_bolus_report.json"

recommendations = parse_report_and_run(path, name)

plot_graph(
    recommendations.get("insulin_effect_dates"),
    recommendations.get("insulin_effect_values"),
    title="Insulin Effect"
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
    line_color="#5ac6fa"
    )
