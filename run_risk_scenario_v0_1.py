#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 13:17:53 2020

@author: ed
"""


# %% LOAD LIBRARIES, FUNCTIONS, AND DATA
import os
import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from plotly.offline import plot
import pdb
from dose import DoseType
from loop_data_manager import update


# %% create pandas dataframes from the input data
# NOTE: move this up into the cell above LATER
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


def create_contiguous_ts(date_min, date_max, freq="1s"):
    date_range = pd.date_range(
        date_min,
        date_max,
        freq=freq
    )

    contig_ts = pd.DataFrame(date_range, columns=["datetime"])
    contig_ts["time"] = contig_ts["datetime"].dt.time

    return contig_ts


def get_setting(current_time, df, setting_value_name, setting_time_name):
    continguous_ts = create_contiguous_ts(
        current_time.date(),
        current_time.date() + datetime.timedelta(days=1),
        freq="1s"
    )
    df_ts = pd.merge(
        continguous_ts,
        df,
        left_on="time",
        right_on=setting_time_name,
        how="left"
    )
    df_ts[setting_value_name].fillna(method='ffill', inplace=True)
    setting_value_at_current_time = (
        df_ts.loc[
            df_ts["datetime"] == current_time, setting_value_name
        ].values[0]
    )
    setting_value_at_current_time

    return setting_value_at_current_time


def simple_metabolism_model(
    carb_amount=0,  # grams (g)
    insulin_amount=np.nan,  # units of insulin (U)
    CIR=12.5,  # carb-to-insulin-ratio (g/U)
    ISF=50,  # insulin sensitivity factor (mg/dL/U)
):
    # create a time series
    t = np.arange(0, 8*60, 1)  # in minutes
    t_5min = np.arange(0, 8*60, 5)

    # if insulin amount is not given,
    # calculate carb amount like a bolus calculator
    if np.isnan(insulin_amount):
        insulin_amount = carb_amount / CIR  # insulin amount

    # insulin model
    if insulin_amount != 0:

        # model constants
        tau1 = 55
        tau2 = 70
        Kcl = 1

        insulin_equation = (
            insulin_amount
            * (1 / (Kcl * (tau2 - tau1)))
            * (np.exp(-t/tau2) - np.exp(-t/tau1))
        )

        ia = np.cumsum(insulin_equation)
        iob = insulin_amount - ia
        iob_5min = iob[t_5min]
        insulin_effect = -ISF * ia
        ie_5min = insulin_effect[t_5min]
        decrease_due_to_insulin = np.append(0, ie_5min[1:] - ie_5min[:-1])

    else:
        decrease_due_to_insulin = np.zeros(len(t_5min))
        iob_5min = np.zeros(len(t_5min))

    # carb model
    if carb_amount > 0:
        K = ISF / CIR  # carb gain
        tau = 42
        theta = 20
        c_t = K*carb_amount*(1-np.exp((theta-t)/tau))*np.heaviside(t-theta, 1)
        ce_5min = c_t[t_5min]
        increase_due_to_carbs = np.append(0, ce_5min[1:] - ce_5min[:-1])

    else:
        increase_due_to_carbs = np.zeros(len(t_5min))

    net_change_in_bg = decrease_due_to_insulin + increase_due_to_carbs

    return net_change_in_bg, t_5min, carb_amount, insulin_amount, iob_5min


def get_bgri(bg_df):
    # Calculate LBGI and HBGI using equation from
    # Clarke, W., & Kovatchev, B. (2009)
    bgs = bg_df.copy()
    bgs[bgs < 1] = 1  # this is added to take care of edge case BG <= 0
    transformed_bg = 1.509*((np.log(bgs)**1.084)-5.381)
    risk_power = 10*(transformed_bg)**2
    low_risk_bool = transformed_bg < 0
    high_risk_bool = transformed_bg > 0
    rlBG = risk_power * low_risk_bool
    rhBG = risk_power * high_risk_bool
    LBGI = np.mean(rlBG)
    HBGI = np.mean(rhBG)
    BGRI = LBGI + HBGI

    return LBGI, HBGI, BGRI


def lbgi_risk_score(lbgi):
    if lbgi > 10:
        risk = 4
    elif lbgi > 5:
        risk = 3
    elif lbgi > 2.5:
        risk = 2
    elif lbgi > 0:
        risk = 1
    else:
        risk = 0
    return risk


def hbgi_risk_score(hbgi):
    if hbgi > 18:
        risk = 4
    elif hbgi > 9:
        risk = 3
    elif hbgi > 4.5:
        risk = 2
    elif hbgi > 0:
        risk = 1
    else:
        risk = 0
    return risk


def suspend_risk_score(minutes_of_suspend):
    if minutes_of_suspend >= 8 * 60:
        risk = 4
    elif minutes_of_suspend >= 5 * 60:
        risk = 3
    elif minutes_of_suspend >= 2 * 60:
        risk = 2
    elif minutes_of_suspend >= 1 * 60:
        risk = 1
    else:
        risk = 0
    return risk


# %%  USER INPUTS
scenario_number = 9  # see list below
simulation_duration_hours = 8


# %% CREATE PATHS, DATAFRAMES, AND LOAD SCENARIO
# select a scenario scenario
path = os.path.join(".", "example_files")
# load in example scenario files
scenario_file_names = [
    "simulation-template.csv",
    "Scenario-1-sensor-inaccurate.csv",
    "Scenario-2-watch-comm - inputs.csv",
    "Scenario-3-accessibility - inputs.csv",
    "Scenario-4-insulin-rationing - inputs.csv",
    "Scenario-5-EM-interference - inputs.csv",
    "Scenario-6-malware-bolus - inputs.csv",
    "Scenario-7-bolus-cancel-fails - inputs.csv",
    "Scenario-8-Loop-loss - no file for this one.csv",
    "Scenario-9-double-carb-entry - inputs.csv",
    "Scenario-9-double-carb-entry-old.csv",
    "Scenario-1A-sensor-inaccurate - inputs.csv",
    "Scenario-1B-sensor-inaccurate - inputs.csv",
]
print("loading scenario: {}\n".format(scenario_file_names[scenario_number]))
table_path_name = os.path.join(path, scenario_file_names[scenario_number])
custom_table_df = pd.read_csv(table_path_name, index_col=0)

# create output dataframes
metab_dur_mins = 8 * 60  # 8 hours
sim_dur_mins = np.max([simulation_duration_hours * 60, metab_dur_mins])

delta_bgs_df = pd.DataFrame(
    index=np.arange(0, sim_dur_mins*2, 5)
)
iob_df = delta_bgs_df.copy()
sim_df = pd.DataFrame(index=np.arange(0, sim_dur_mins, 5))
scenario_results = pd.DataFrame()

# get inputs from custom scenario
inputs_from_file = input_table_to_dict(custom_table_df)

# convert inputs to dataframes
(
     basal_rates, carb_events, carb_ratios, dose_events, cgm_df,
     df_last_temporary_basal, df_misc, isfs,
     df_settings, df_target_range
) = dict_inputs_to_dataframes(inputs_from_file)


# %% RUN INITIAL SCENARIO THROUGH DIABETES METABOLISM MODEL
print("running scenario through simple diabetes metabolism model...")
t0 = inputs_from_file.get("time_to_calculate_at")
bg_t0_actual = cgm_df.loc[
    cgm_df["glucose_dates"] == t0, "actual_blood_glucose"
].values[0]

bg_t0_loop = cgm_df.loc[
    cgm_df["glucose_dates"] == t0, "glucose_values"
].values[0]

carb_amount_actual = carb_events.loc[
    carb_events["carb_dates"] == t0, "actual_carbs"
].values[0]

insulin_amount_actual = dose_events.loc[
    dose_events["dose_start_times"] == t0,
    "actual_doses"
].values[0]

cir_index = carb_ratios[
    t0.time() >= carb_ratios["carb_ratio_start_times"]
].index.values.min()
cir_actual = carb_ratios.loc[cir_index, "actual_carb_ratios"]

isf_index = isfs[
    t0.time() >= isfs["sensitivity_ratio_start_times"]
].index.values.min()
isf_actual = isfs.loc[isf_index, "actual_sensitivity_ratios"]

delta_bg, ts, carbs_consumed, insulin_delivered, iob = simple_metabolism_model(
    carb_amount=carb_amount_actual,
    insulin_amount=insulin_amount_actual,
    CIR=cir_actual,
    ISF=isf_actual,
)

delta_bgs_df["initial_scenario"] = np.nan
bg_times = (
    (delta_bgs_df.index >= 0) &
    (delta_bgs_df.index < metab_dur_mins)
)
delta_bgs_df.loc[bg_times, "initial_scenario"] = delta_bg

# capture the insulin that will be onboard for the next 8 hours
iob_df["initial_scenario"] = np.nan
iob_df.loc[bg_times, "initial_scenario"] = iob

bg_timeseries = bg_t0_actual + np.cumsum(delta_bg)
sim_df.loc[bg_times, "pump_bgs"] = bg_timeseries
pump_LBGI, pump_HBGI, pump_BGRI = get_bgri(bg_timeseries)

scenario_results.loc["LBGI", "pumpValue"] = pump_LBGI
scenario_results.loc["LBGI", "pumpRiskScore"] = lbgi_risk_score(pump_LBGI)
scenario_results.loc["HBGI", "pumpValue"] = pump_HBGI
scenario_results.loc["HBGI", "pumpRiskScore"] = hbgi_risk_score(pump_HBGI)
scenario_results.loc["BGRI", "pumpValue"] = pump_BGRI

print("risk of scenario in a pump only or mdi situation:")
print(scenario_results, "\n")


# %% RUN THE INITIAL SCENARIO THROUGH PYLOOPKIT
print("simulating the scenario through pyloopkit over {} hours:".format(
    simulation_duration_hours)
)

loop_algorithm_output = update(inputs_from_file)
inputs = loop_algorithm_output.get("input_data")

# get scheduled basal rate in loop
sbr_index = basal_rates[
    t0.time() >= basal_rates["basal_rate_start_times"]
].index.values.min()
sbr_loop = basal_rates.loc[sbr_index, "basal_rate_values"]
sbr_actual = basal_rates.loc[sbr_index, "actual_basal_rates"]

if loop_algorithm_output.get("recommended_temp_basal") is None:
    loop_temp_basal = sbr_loop
else:
    loop_temp_basal, _ = (
        loop_algorithm_output.get("recommended_temp_basal")
    )

# get the insulin amount delivered (by loop) in the next 5 minutes
# relative to user's actual (scheduled) basal rate
temp_basal_insulin_amount = (loop_temp_basal - sbr_actual) / 12

# get the initial loop parameters
carb_amount_loop = carb_events.loc[
    carb_events["carb_dates"] == t0, "carb_values"
].values[0]

insulin_amount_loop = dose_events.loc[
    dose_events["dose_start_times"] == t0,
    "dose_values"
].values[0]

cir_loop = carb_ratios.loc[cir_index, "carb_ratio_values"]
isf_loop = isfs.loc[isf_index, "sensitivity_ratio_values"]

# write the initial parameters to the simulation output
sim_df.loc[0, "bg_actual"] = bg_t0_actual
sim_df.loc[0, "bg_loop"] = bg_t0_loop
sim_df.loc[0, "temp_basal"] = loop_temp_basal
sim_df.loc[0, "insulin_relative_to_actual_basal"] = temp_basal_insulin_amount
sim_df.loc[0, "iob"] = insulin_amount_actual
sim_df.loc[0, "carbLoop"] = carb_amount_loop
sim_df.loc[0, "carbActual"] = carb_amount_actual
sim_df.loc[0, "insulinLoop"] = insulin_amount_loop
sim_df.loc[0, "insulinActual"] = insulin_amount_actual
sim_df.loc[0, "cirLoop"] = cir_loop
sim_df.loc[0, "cirActual"] = cir_actual
sim_df.loc[0, "isfLoop"] = isf_loop
sim_df.loc[0, "isfActual"] = isf_actual
sim_df.loc[0, "sbrLoop"] = sbr_loop
sim_df.loc[0, "sbrActual"] = sbr_actual


# %% SIMULATE OVER THE NEXT <USER INPUT> HOURS
for t in np.arange(0, sim_dur_mins, 5):
    # ADD TEMP BASAL RECOMMENDATION FROM PYLOOPKIT TO SDMBC
    # run the scenario through simple metabolism model
    delta_bg, _, _, _, _ = simple_metabolism_model(
        carb_amount=0,
        insulin_amount=temp_basal_insulin_amount,
        CIR=cir_actual,
        ISF=isf_actual,
    )

    # get insulin on board due to temp basal
    _, _, _, _, iob = simple_metabolism_model(
        carb_amount=0,
        insulin_amount=loop_temp_basal,
        CIR=cir_actual,
        ISF=isf_actual,
    )

    delta_bgs_df["t={}".format(t)] = np.nan
    bg_times = (
        (delta_bgs_df.index >= t) & (delta_bgs_df.index < (t + metab_dur_mins))
    )
    delta_bgs_df.loc[bg_times, "t={}".format(t)] = delta_bg

    next_bg_actual = (
        sim_df.loc[t, "bg_actual"]
        + delta_bgs_df.loc[delta_bgs_df.index == (t+5)].sum(axis=1).values[0]
    )

    next_bg_loop = (
        sim_df.loc[t, "bg_loop"]
        + delta_bgs_df.loc[delta_bgs_df.index == (t+5)].sum(axis=1).values[0]
    )

    sim_df.loc[t+5, "bg_actual"] = next_bg_actual
    sim_df.loc[t+5, "bg_loop"] = next_bg_loop

    iob_df["t={}".format(t)] = np.nan
    iob_df.loc[bg_times, "t={}".format(t)] = iob / 12
    sim_df.loc[t, "iob"] = (
        iob_df.loc[iob_df.index == (t)].sum(axis=1).values[0]
    )

    # APPEND TB(t) and BG(t+5) TO PYLOOPKIT DATA AND RERUN LOOP ALGORITHM
    # add the temp basal implemented by loop to the scenario
    current_time = t0 + datetime.timedelta(minutes=np.int(t))
    next_time = t0 + datetime.timedelta(minutes=np.int(t+5))
    inputs_from_file["time_to_calculate_at"] = next_time
    inputs_from_file["dose_types"].append(DoseType.tempbasal)
    inputs_from_file["dose_start_times"].append(current_time)
    inputs_from_file["dose_end_times"].append(next_time)
    inputs_from_file["dose_values"].append(loop_temp_basal)
    inputs_from_file["glucose_dates"].append(next_time)
    inputs_from_file["glucose_values"].append(
        np.max([40, np.min([400, np.round(next_bg_loop)])])
    )

    # run the loop algorithm again at next_time
    loop_algorithm_output = update(inputs_from_file)
    inputs = loop_algorithm_output.get("input_data")

    # get scheduled basal rate in loop
    sbr_index = basal_rates[
        next_time.time() >= basal_rates["basal_rate_start_times"]
    ].index.values.min()
    sbr_loop = basal_rates.loc[sbr_index, "basal_rate_values"]
    sbr_actual = basal_rates.loc[sbr_index, "actual_basal_rates"]

    if loop_algorithm_output.get("recommended_temp_basal") is None:
        loop_temp_basal = sbr_loop
    else:
        loop_temp_basal, _ = (
            loop_algorithm_output.get("recommended_temp_basal")
        )

    # get the insulin amount delivered (by loop) in the next 5 minutes
    # relative to user's actual (scheduled) basal rate
    temp_basal_insulin_amount = (loop_temp_basal - sbr_actual) / 12

    # get the loop parameters at time t=current_time
    carbs_at_next_time = (carb_events["carb_dates"] == next_time).values[0]
    if carbs_at_next_time:
        carb_amount_loop = carb_events.loc[
            carbs_at_next_time, "carb_values"
        ].values[0]

        carb_amount_actual = carb_events.loc[
            carbs_at_next_time, "actual_carbs"
        ].values[0]

    else:
        carb_amount_loop, carb_amount_actual = 0, 0

    bolus_at_next_time = (
        dose_events["dose_start_times"] == next_time
    ).values[0]

    if bolus_at_next_time:
        insulin_amount_loop = dose_events.loc[
            bolus_at_next_time,
            "dose_values"
        ].values[0]

        insulin_amount_actual = dose_events.loc[
            bolus_at_next_time,
            "actual_doses"
        ].values[0]

    else:
        insulin_amount_loop, insulin_amount_actual = 0, 0

    cir_index = carb_ratios[
        next_time.time() >= carb_ratios["carb_ratio_start_times"]
    ].index.values.min()
    cir_actual = carb_ratios.loc[cir_index, "actual_carb_ratios"]

    isf_index = isfs[
        next_time.time() >= isfs["sensitivity_ratio_start_times"]
    ].index.values.min()
    isf_actual = isfs.loc[isf_index, "actual_sensitivity_ratios"]

    cir_loop = carb_ratios.loc[cir_index, "carb_ratio_values"]
    isf_loop = isfs.loc[isf_index, "sensitivity_ratio_values"]

    # write parameters to the simulation output
    sim_df.loc[t+5, "temp_basal"] = loop_temp_basal
    sim_df.loc[t+5, "insulin_relative_to_actual_basal"] = (
        temp_basal_insulin_amount
    )
    sim_df.loc[t+5, "iob"] = insulin_amount_actual
    sim_df.loc[t+5, "carbLoop"] = carb_amount_loop
    sim_df.loc[t+5, "carbActual"] = carb_amount_actual
    sim_df.loc[t+5, "insulinLoop"] = insulin_amount_loop
    sim_df.loc[t+5, "insulinActual"] = insulin_amount_actual
    sim_df.loc[t+5, "cirLoop"] = cir_loop
    sim_df.loc[t+5, "cirActual"] = cir_actual
    sim_df.loc[t+5, "isfLoop"] = isf_loop
    sim_df.loc[t+5, "isfActual"] = isf_actual
    sim_df.loc[t+5, "sbrLoop"] = sbr_loop
    sim_df.loc[t+5, "sbrActual"] = sbr_actual

    print("t={}, tempBasal={} U/hr, BG(t+5)=>actual={}, loop={} mg/dL".format(
        t, loop_temp_basal,
        np.int(np.round(next_bg_actual)), np.int(np.round(next_bg_loop))
    ))

# %% SUMMARIZE & SAVE RESULTS
# get BGRIs (risk of hypo and hyperglycemia)
scenario_LBGI, scenario_HBGI, scenario_BGRI = get_bgri(sim_df["bg_actual"])
scenario_results.loc["LBGI", "loopValue"] = scenario_LBGI
scenario_results.loc["LBGI", "loopRiskScore"] = lbgi_risk_score(scenario_LBGI)
scenario_results.loc["HBGI", "loopValue"] = scenario_HBGI
scenario_results.loc["HBGI", "loopRiskScore"] = hbgi_risk_score(scenario_HBGI)
scenario_results.loc["BGRI", "loopValue"] = scenario_BGRI

# get risk of DKA
minutes_of_zero_temp_basal = (
    np.sum((sim_df["insulinActual"] == 0) & (sim_df["temp_basal"] == 0)) * 5
)
scenario_results.loc["minutes_of_zero_temp_basal", "loopValue"] = (
    minutes_of_zero_temp_basal
)
scenario_results.loc["minutes_of_zero_temp_basal", "loopRiskScore"] = (
    suspend_risk_score(minutes_of_zero_temp_basal)
)

scenario_results.loc["minutes_of_zero_iob", "loopValue"] = (
    np.sum(sim_df.loc[0:(sim_dur_mins-5), "iob"] == 0) * 5
)

print("\n")
print("simulation complete, here are the results:")
print(scenario_results.iloc[:, 2:])

# save results
scenario_results.to_csv(table_path_name + ".scenario_results.csv")
sim_df.to_csv(table_path_name + ".sim_df.csv")
iob_df.to_csv(table_path_name + ".iob_df.csv")
delta_bgs_df.to_csv(table_path_name + ".delta_bgs_df.csv")
