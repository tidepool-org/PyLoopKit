from pyloopkit.tidepool_api.tidepool_api import TidepoolAPI
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot

from pyloopkit.dose import DoseType
from pyloopkit.generate_graphs import plot_graph, plot_loop_inspired_glucose_graph
#from .loop_kit_tests import find_root_path
from pyloopkit.loop_math import predict_glucose

from pyloopkit.tidepool_api_parser import (
    parse_report_and_run
)

# Load data from Tidepool API
# Remember, this is for testing purposes, never post the code containing sensitive information
EMAIL = 'YOUR_TIDEPOOL_EMAIL'
PASSWORD = 'YOUR_TIDEPOOL_PASSWORD'

tp_api = TidepoolAPI(EMAIL, PASSWORD)
tp_api.login()

# Default use the data from the last 24 hours
start_date = datetime.now() - timedelta(days=1)
end_date = datetime.now()

# Uncomment the lines below to customize days
#start_date = datetime(2023, 2, 4)
#end_date = datetime(2023, 2, 5) # year, month, day

# All the data in json format
user_data = tp_api.get_user_event_data(start_date, end_date)

tp_api.logout()

# Define the time at which you want to see the predictions
#time_to_run = datetime(2023, 2, 5, 8, 25)
time_to_run = None

# uncomment parse_dictionary_from_previous_run if using data from a previous run
recommendations = parse_report_and_run(user_data, time_to_run=time_to_run)
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








