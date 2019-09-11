#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2019-09-10

@author: ed nykaza
"""
# pylint: disable=C0103
import os
import datetime
import pandas as pd
import numpy as np
from pyloop_parser import parse_report_and_run
from loop_data_manager import update
from dose import DoseType


# %% create pandas dataframes from the input data
def dict_inputs_to_dataframes(input_data):
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
                # TODO: change how this is dealt with in pyloopkit
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
                            df_settings.loc[sk, "settings"] = (
                                settings_dictionary.get(sk)[0]
                            )
                        else:
                            df_settings.loc[sk, "settings"] = (
                                settings_dictionary.get(sk)
                            )
                    else:
                        if sk in ["model", "default_absorption_times"]:
                            # TODO: change this in the loop algorithm
                            # to take 2 to 3 inputs instead of 1
                            df_settings.loc[sk, "settings"] = (
                                str(settings_dictionary.get(sk))
                            )

    return (
        df_basal_rate, df_carb, df_carb_ratio, df_dose, df_glucose,
        df_last_temporary_basal, df_misc, df_sensitivity_ratio,
        df_settings, df_target_range
    )


def dataframe_inputs_to_dict(dfs, df_misc, df_settings):
    # write the dataframes back to one dictionary
    input_dictionary = dict()
    input_dictionary = df_misc.to_dict()[0]
    for df in dfs:
        for col in df.columns:
            if "units" not in col:
                input_dictionary[col] = df[col].tolist()
            else:
                input_dictionary[col] = df[col].unique()[0]

    input_dictionary["settings_dictionary"] = df_settings.to_dict()["settings"]

    # set the format back for the edge cases
    input_dictionary["settings_dictionary"]["model"] = np.safe_eval(
        input_dictionary["settings_dictionary"]["model"]
    )
    input_dictionary["settings_dictionary"]["default_absorption_times"] = (
        np.safe_eval(
            input_dictionary["settings_dictionary"]["default_absorption_times"]
        )
    )

    input_dictionary["offset_applied_to_dates"] = (
        int(input_dictionary["offset_applied_to_dates"])
    )

    return input_dictionary


def input_dict_to_one_dataframe(input_data):
    # get dataframes from input
    (
        df_basal_rate, df_carb, df_carb_ratio, df_dose, df_glucose,
        df_last_temporary_basal, df_misc, df_sensitivity_ratio,
        df_settings, df_target_range
    ) = dict_inputs_to_dataframes(input_data)

    # combine the dataframes into one big dataframe,
    # put glucose at end since that trace is typically long
    combined_df = pd.DataFrame()
    combined_df = pd.concat([combined_df, df_settings])
    combined_df = pd.concat([combined_df, df_misc])

    dfs = [
       df_basal_rate, df_carb, df_carb_ratio, df_dose,
       df_last_temporary_basal, df_sensitivity_ratio,
       df_target_range, df_glucose
    ]

    for df in dfs:
        combined_df = pd.concat([combined_df, df.T])

    # move settings back to the front of the dataframe
    combined_df = combined_df[np.append("settings", combined_df.columns[0:-1])]

    return combined_df


def str2bool(string_):
    return string_.lower() in ("yes", "true", "t", "1")


def input_table_to_dict(input_df):
    dict_ = dict()

    # first parse and format the settings
    all_settings = input_df["settings"].dropna()
    dict_["settings_dictionary"] = all_settings.to_dict()

    for k in dict_["settings_dictionary"].keys():
        if k in [
            "dynamic_carb_absorption_enabled",
            "retrospective_correction_enabled"
        ]:

            dict_["settings_dictionary"][k] = str2bool(
                dict_["settings_dictionary"][k]
            )
        else:
            dict_["settings_dictionary"][k] = np.safe_eval(
                dict_["settings_dictionary"][k]
            )
    if "suspend_threshold" not in dict_["settings_dictionary"].keys():
        dict_["settings_dictionary"]["suspend_threshold"] = None

    # then parse and format the rest
    input_df_T = (
        input_df.drop(columns=["settings"]).dropna(axis=0, how="all").T
    )

    input_df_columns = input_df_T.columns
    for col in input_df_columns:
        if "units" in col:
            dict_[col] = input_df_T[col].dropna().unique()[0]
        elif "offset" in col:
            dict_[col] = int(np.safe_eval(input_df_T[col].dropna()[0]))
        elif "time_to_calculate" in col:
            dict_[col] = (
                datetime.datetime.fromisoformat(
                    pd.to_datetime(input_df_T[col].dropna()[0]).isoformat()
                )
            )
        else:
            temp_df = input_df_T[col].dropna()
            temp_array = []
            for v in temp_df.values:
                if ":" in v:
                    if len(v) == 7:
                        obj = (
                            datetime.time.fromisoformat(
                                pd.to_datetime(v).strftime("%H:%M:%S")
                            )
                        )
                    elif len(v) == 8:
                        obj = datetime.time.fromisoformat(v)
                    elif len(v) > 8:
                        obj = (
                            datetime.datetime.fromisoformat(
                                pd.to_datetime(v).isoformat()
                            )
                        )
                    else:
                        obj = np.safe_eval(v)
                elif "DoseType" in v:
                    obj = DoseType.from_str(v[9:])
                else:
                    obj = np.safe_eval(v)

                temp_array = np.append(temp_array, obj)

            dict_[col] = list(temp_array)

    return dict_


# %% load in example file(s)
''''select the exmaple file you want to run/test'''
# TODO: Russ, can you make this a test, could run through all 3 examples
# and the functions should all pass
example_files = [
    "example_issue_report_1.json",
    "example_issue_report_2.json",
    "example_issue_report_3.json"
]

name = example_files[2]
path = os.path.join(".", "example_files")

# run the Loop algorithm with the issue report data
loop_output = parse_report_and_run(path, name)

# get just the input data
input_data = loop_output.get("input_data")

# double check that the input data can be used to re-run the scenario
new_loop_output = update(input_data)

# TODO: make this a test, should be something like:
assert(loop_output == new_loop_output)


# %% test the functions
'''test dict_inputs_to_dataframes & dataframe_inputs_to_dict:
    the input dictionaries should be the same after converting to
    dataframes and then back to one dictionary
'''
# convert dict_inputs_to_dataframes
(
 df_basal_rate, df_carb, df_carb_ratio, df_dose, df_glucose,
 df_last_temporary_basal, df_misc, df_sensitivity_ratio,
 df_settings, df_target_range
) = dict_inputs_to_dataframes(input_data)

input_dataframes = [
   df_basal_rate, df_carb, df_carb_ratio, df_dose, df_glucose,
   df_last_temporary_basal, df_sensitivity_ratio, df_target_range
]

# convert dataframe_inputs_to_dict
input_dict = dataframe_inputs_to_dict(input_dataframes, df_misc, df_settings)
# TODO: make this a test, should be something like:
assert(input_dict == input_data)

'''test input_dict_to_one_dataframe & input_table_to_dict
'''
big_df = input_dict_to_one_dataframe(input_data)
table_name = name + "-input_data_table.csv"
table_path_name = os.path.join(path, table_name)
big_df.to_csv(table_path_name)

# let's load the data in from file and get it back in the right format
# so we know that this will work for when we have custom files
input_table_df = pd.read_csv(table_path_name, index_col=0)
from_file_dict = input_table_to_dict(input_table_df)

assert(from_file_dict == input_data)

# triple check that the input data from file can be used to re-run the scenario
newest_loop_output = update(from_file_dict)

# TODO: make this a test, should be something like:
assert(loop_output == newest_loop_output)

# test using custom input templates
cutom_scenario_files = [
    "custom-scenario-table-template-simple.csv",
    "custom-scenario-table-template-complex.csv",
]
table_path_name = os.path.join(path, cutom_scenario_files[0])
custom_table_df = pd.read_csv(table_path_name, index_col=0)
cumstom_file_dict = input_table_to_dict(custom_table_df)
custom_output = update(cumstom_file_dict)
