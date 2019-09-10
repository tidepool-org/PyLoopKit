#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2019-09-10

@author: ed nykaza
"""
# pylint: disable=C0103
import json
import os
import datetime
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot

from dose import DoseType
from generate_graphs import plot_graph, plot_loop_inspired_glucose_graph
from loop_kit_tests import find_root_path
from loop_math import predict_glucose
from pyloop_parser import (
    parse_report_and_run, parse_dictionary_from_previous_run
)
from loop_data_manager import update

import pdb



# %% find the path to the file in the repo
# uncomment the name of the file you'd like to run
#name = "example_issue_report_1.json"
#name = "example_issue_report_2.json"
name = "example_issue_report_3.json"
# name = "example_from_previous_run.json"
#name = "example_issue_report_3.json"
path = os.path.join(".", "example_files")

# run the Loop algorithm with the issue report data

# uncomment parse_report_and_run if using an issue report; uncomment
# parse_dictionary_from_previous_run if using data from a previous run
recommendations = parse_report_and_run(path, name)
input_data = recommendations.get("input_data")


# %% first double check that the input data can be used to re-run the scenario
new_recommendations = update(input_data)
# TODO: Russ, can you make this a test, should be something like:
assert(recommendations == new_recommendations)


# define the dataframes to store the data in
df_basal_rate = pd.DataFrame()
df_carb = pd.DataFrame()
df_carb_ratio = pd.DataFrame()
df_dose = pd.DataFrame()
df_glucose = pd.DataFrame()
df_last_temporary_basal = pd.DataFrame()
df_misc = pd.DataFrame()
df_sensitivity_ratio = pd.DataFrame()
df_settings = pd.DataFrame()
df_target_range = pd.DataFrame()

for k in input_data.keys():
    if type(input_data[k]) != dict:
        if "basal_rate" in k:
            df_basal_rate[k] = input_data.get(k)
        elif "carb_ratio" in k:
            df_carb_ratio[k] = input_data.get(k)
        elif "carb" in k:
            df_carb[k] = input_data.get(k)
        elif "dose" in k:
            df_dose[k] = input_data.get(k)
        elif "glucose" in k:
            df_glucose[k] = input_data.get(k)
        elif "last_temporary_basal" in k:
            # TODO: fix this edge case
            df_last_temporary_basal[k] = input_data.get(k)
        elif "sensitivity_ratio" in k:
            df_sensitivity_ratio[k] = input_data.get(k)
        elif "target_range" in k:
            df_target_range[k] = input_data.get(k)
        else:
            if np.size(input_data.get(k)) == 1:
                if type(input_data[k]) == list:
                    df_misc.loc[k, 0] = input_data.get(k)[0]
                else:
                    df_misc.loc[k, 0] = input_data.get(k)
    else:
        if "settings_dictionary" in k:
            settings_dictionary = input_data.get("settings_dictionary")
            for sk in settings_dictionary.keys():
                if np.size(settings_dictionary.get(sk)) == 1:
                    if type(settings_dictionary[sk]) == list:
                        df_settings.loc[sk, "settings"] = settings_dictionary.get(sk)[0]
                    else:
                        df_settings.loc[sk, "settings"] = settings_dictionary.get(sk)
                else:
                    if sk in ["model", "default_absorption_times"]:
                        # TODO: change this in the loop algorithm to take 2/3 inputs instead of 1
                        df_settings.loc[sk, "settings"] = str(settings_dictionary.get(sk))



# %% write the dataframes back to one dictionary
dfs = [
   df_basal_rate, df_carb, df_carb_ratio, df_dose, df_glucose,
   df_last_temporary_basal, df_sensitivity_ratio, df_target_range
]

test_dict = dict()
test_dict = df_misc.to_dict()[0]
for df in dfs:
    for col in df.columns:
        if "units" not in col:
            test_dict[col] = df[col].tolist()
        else:
            test_dict[col] = df[col].unique()[0]

test_dict["settings_dictionary"] = df_settings.to_dict()["settings"]

# set the format back for the edge cases
test_dict["settings_dictionary"]["model"] = np.safe_eval(
    test_dict["settings_dictionary"]["model"]
)
test_dict["settings_dictionary"]["default_absorption_times"] = np.safe_eval(
    test_dict["settings_dictionary"]["default_absorption_times"]
)
test_dict["offset_applied_to_dates"] = int(test_dict["offset_applied_to_dates"])

# TODO: Russ, can you make this a test, should be something like:
assert(test_dict == input_data)


# %% now let's combine the dataframes into one big dataframe,
# put glucose at end since that trace is typically long
combined_df = pd.DataFrame()
combined_df = pd.concat([combined_df, df_settings])
combined_df = pd.concat([combined_df, df_misc])

dfs = [
   df_basal_rate, df_carb, df_carb_ratio, df_dose,
   df_last_temporary_basal, df_sensitivity_ratio, df_target_range, df_glucose
]


for df in dfs:
    combined_df = pd.concat([combined_df, df.T])

# move settings back to the front of the dataframe
combined_df = combined_df[np.append("settings", combined_df.columns[0:-1])]
combined_df.to_csv("test_combined.csv")


# %% let's load the data in from file and get it back in the right format
# so we know that this will work for when we have custom files
from_file_dict = dict()

all_df = pd.read_csv("test_combined.csv", index_col=0)
all_settings = all_df["settings"].dropna()
from_file_dict["settings_dictionary"] = all_settings.to_dict()

all_df_T = all_df.drop(columns=["settings"]).dropna(axis=0, how="all").T
all_df_columns = all_df_T.columns


for col in all_df_columns:
    if "units" not in col:
        from_file_dict[col] = all_df_T[col].dropna().tolist()
    else:
        from_file_dict[col] = all_df_T[col].unique()[0]

# put some of the values back in the right format
# HERE IS THE VERY NEXT ACTION

from_file_dict["settings_dictionary"]["model"] = np.safe_eval(
    from_file_dict["settings_dictionary"]["model"]
)

assert(from_file_dict == input_data)

# %%

