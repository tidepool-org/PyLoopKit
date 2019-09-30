#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 11 14:53:05 2019

@author: ed
"""
import os
import datetime
import pandas as pd
import numpy as np
from input_data_tools import dict_inputs_to_dataframes, input_table_to_dict
from loop_data_manager import update
from loop_math import predict_glucose
from insulin_math import insulin_on_board
import plotly.graph_objs as go
from plotly.offline import plot


# %% functions
def prepare_bg(df, current_time):

    df_trace = go.Scattergl(
        name="bg",
        x=df["glucose_dates"],
        y=df["glucose_values"],
        hoverinfo="y+name+x",
        mode='markers',
        marker=dict(
            size=6,
            line=dict(width=0),
            color="#7A68B3"
        )
    )

    df_axis = dict(
            domain=[0.5, 1],
            range=[0, 400],
            tickvals=[-100, 54, 70, 140, 180, 250, 400],
            fixedrange=True,
            hoverformat=".0f",
            zeroline=False,
            showgrid=True,
            gridcolor="#c0c0c0",
            title=dict(
                text="Blood Glucose<br>(mg/dL)",
                font=dict(
                    size=12
                )
            )
        )

    df_annotations = go.layout.Annotation(
        x=current_time,
        y=df["glucose_values"].values[-1] + 10,
        xref="x",
        yref="y2",
        text="evaluation point",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ayref="y2",
        ay=425
    )

    df_trace.yaxis = "y2"

    return df, df_trace, df_axis, df_annotations


def create_contiguous_ts(date_min, date_max, freq="1s"):
    date_range = pd.date_range(
        date_min,
        date_max,
        freq=freq
    )

    contig_ts = pd.DataFrame(date_range, columns=["datetime"])
    contig_ts["time"] = contig_ts["datetime"].dt.time

    return contig_ts


def convert_times_and_types(obj):
    """ Convert dose types into strings """
    return str(obj.name)


def downsample(df, current_time, freq="5min"):
    df_range = pd.date_range(
        df["datetime"].min(),
        current_time,
        freq=freq
    )

    df = pd.merge(
        pd.DataFrame(df_range, columns=["datetime"]),
        df,
        on="datetime",
        how="left"
    )

    # add back in the current time
    last_index = df.index.max()
    if df.loc[last_index, "datetime"] != current_time:
        df.loc[last_index + 1, :] = df.loc[last_index, :]
        df.loc[last_index + 1, "datetime"] = current_time

    return df


def make_basal_traces(df, value_name, trace_name):
    if "scheduled" in trace_name:
        dash = "dot"
        width = 1
        fill = 'none'
        opacity = 0.75
    else:
        dash = "solid"
        width = 1
        fill = 'tozeroy'
        opacity = 0.25

    b_traces = []
    for i in range(0, len(df)):

        if i < len(df)-1:
            legend_on = False
            x_vals = [
                df["datetime"][i],
                df["datetime"][i+1],
                df["datetime"][i+1],
            ]

            y_vals = [
                df[value_name][i],
                df[value_name][i],
                df[value_name][i+1],
            ]

        else:
            legend_on = True
            x_vals = [
                df["datetime"][i],
            ]

            y_vals = [
                df[value_name][i],
            ]

        tmp_trace = go.Scatter(
            name=trace_name,
            legendgroup=trace_name,
            showlegend=legend_on,
            mode='lines',
            x=x_vals,
            y=y_vals,
            hoverinfo="none",
            line=dict(
                shape='vh',
                color='#5691F0',
                dash=dash,
                width=width,
            ),
            fill=fill,
            fillcolor='rgba(86,145,240,{})'.format(opacity)
        )

        tmp_trace.yaxis = "y"

        b_traces.append(tmp_trace)

    return b_traces


def prepare_basal(basal_rates, df_dose, contig_ts, current_time):
    unique_dose_types = df_dose["type"].unique()
    df = pd.merge(
        contig_ts,
        basal_rates,
        left_on="time",
        right_on="basal_rate_start_times",
        how="left"
    )

    df["basal_rate_values"].fillna(method='ffill', inplace=True)
    df.dropna(subset=['basal_rate_values'], inplace=True)

    # temp basal data
    if (
            ("basal" in str(unique_dose_types))
            | ("tempbasal" in unique_dose_types)
            | ("suspend" in unique_dose_types)

    ):
        temp_basal = (
            df_dose[(
                (df_dose["type"] == "basal")
                | (df_dose["type"] == "tempbasal")
                | (df_dose["type"] == "suspend")
            )].copy()
        )

        temp_basal["type"].replace("basal", "temp", inplace=True)
        all_temps = pd.DataFrame()
        for idx in temp_basal.index:
            rng = pd.date_range(
                temp_basal.loc[idx, "dose_start_times"],
                (
                    temp_basal.loc[idx, "dose_end_times"]
                    - datetime.timedelta(seconds=1)
                ),
                freq="1s"
            )
            temp_ts = pd.DataFrame(rng, columns=["datetime"])
            temp_ts["tbr"] = temp_basal.loc[idx, "dose_values"]
            temp_ts["type"] = temp_basal.loc[idx, "type"]
            all_temps = pd.concat([all_temps, temp_ts])

        df = pd.merge(df, all_temps, on="datetime", how="left")
        df["type"].fillna("scheduled", inplace=True)

    else:
        df["tbr"] = np.nan

    df["delivered"] = df["tbr"]
    df.loc[df["delivered"].isnull(), "delivered"] = (
        df.loc[df["delivered"].isnull(), "basal_rate_values"]
    )

    # preapre scheduled basal rate
    sbr_df = df[df["basal_rate_start_times"].notnull()].copy()
    sbr_df.reset_index(drop=True, inplace=True)

    sbr_traces = (
        make_basal_traces(sbr_df, "basal_rate_values", "scheduled basal rate")
    )

    # prepare basal delivered
    basal_df = df[df["datetime"] <= current_time].copy()
    basal_df["transition"] = (
        basal_df["delivered"] != basal_df["delivered"].shift(1)
    )
    basal_df.loc[basal_df.index.max(), "transition"] = True
    basal_df = basal_df[basal_df["transition"]]
    basal_df.reset_index(drop=True, inplace=True)

    basal_traces = (
        make_basal_traces(basal_df, "delivered", "basal delivered")
    )

    return basal_df, sbr_df, basal_traces, sbr_traces


def prepare_bolus(df_dose):
    df = df_dose[df_dose["type"] == "bolus"]

    df_trace = go.Scatter(
        name="bolus",
        showlegend=True,
        mode='markers',
        x=df["dose_start_times"],
        y=df["dose_values"],
                hoverinfo="y+name+x",
        marker=dict(
            symbol='triangle-down',
            size=15 + df["dose_values"],
            color="#5691F0"
        ),
    )

    df_trace.yaxis = "y"

    return df, df_trace


def prepare_carbs(df_events, df_ratios, continguous_ts):
    carb_df = pd.merge(
        continguous_ts,
        df_ratios,
        left_on="time",
        right_on="carb_ratio_start_times",
        how="left"
    )
    carb_df["carb_ratio_values"].fillna(method='ffill', inplace=True)
    carb_df.dropna(subset=['carb_ratio_values'], inplace=True)

    # df events
    carb_df = pd.merge(
        carb_df,
        df_events,
        left_on="datetime",
        right_on="carb_dates",
        how="left",
    )

    # add bolus height for figure
    carb_df["bolus_height"] = (
        carb_df["carb_values"] / carb_df["carb_ratio_values"]
    )

    # TODO: visualize the carb-to-insulin-ratio (cir)
    # in the meantime drop rows where grams is null
    carb_df.dropna(subset=['carb_values'], inplace=True)

    df_trace = go.Scatter(
        name="carbs (g)",
        mode='markers + text',
        x=carb_df["datetime"],
        y=carb_df["bolus_height"] + 0.75,
        hoverinfo="name+x",
        marker=dict(
            color="#0AA648",
            size=25
        ),
        opacity=0.75,
        text=carb_df["carb_values"],
        textposition='middle center'
    )

    df_trace.yaxis = "y"

    return carb_df, df_trace


def prepare_target_range(df_target_range, continguous_ts, current_time):
    df = pd.merge(
        continguous_ts,
        df_target_range,
        left_on="time",
        right_on="target_range_start_times",
        how="left"
    )
    df["target_range_minimum_values"].fillna(method='ffill', inplace=True)
    df["target_range_maximum_values"].fillna(method='ffill', inplace=True)
#    target_at_eval_df = df[df["datetime"] == current_time]
    df.dropna(subset=['target_range_minimum_values'], inplace=True)

    # downsample
    target = df[df["target_range_value_units"].notnull()].copy()
    target.reset_index(drop=True, inplace=True)

    target_traces = []
    for i in range(0, len(target)):
        min_val = target["target_range_minimum_values"][i]
        max_val = target["target_range_maximum_values"][i]
        if max_val - min_val < 5:
            width = 5
        else:
            width = 1

        if i < len(target)-1:
            legend_on = False
            x_vals = [
                target["datetime"][i],
                target["datetime"][i],
                target["datetime"][i+1],
                target["datetime"][i+1],
                target["datetime"][i]
            ]

            y_vals = [
                min_val,
                max_val,
                max_val,
                min_val,
                min_val
            ]

        else:
            legend_on = True
            x_vals = [
                target["datetime"][i],
                target["datetime"][i]
            ]

            y_vals = [
                min_val,
                max_val,
            ]

        tmp_trace = go.Scatter(
            name="correction range",
            legendgroup="correction range",
            showlegend=legend_on,
            mode='lines',
            x=x_vals,
            y=y_vals,
            hoverinfo="none",
            line=dict(
                shape='vh',
                width=width,
                color="rgba(152, 134, 207, 0.25)"
            ),
            fill="tonext",
            fillcolor="rgba(152, 134, 207, 0.125)",
        )

        tmp_trace.yaxis = "y2"
        target_traces.append(tmp_trace)

    return df, target_traces


def prepare_insulin_axis(basal, bolus, carbs, current_time):

    max_value = max(
        basal["basal_rate_values"].max() + 1,
        basal["tbr"].max() + 1,
        carbs["bolus_height"].max() + 2,
        bolus["dose_values"].max() + 2,
    )

    axis = dict(
        domain=[0, 0.2],
        range=[0, max_value],
        fixedrange=True,
        hoverformat=".2f",
        showgrid=True,
        gridcolor="#c0c0c0",
        title=dict(
            text="Events<br>(U, U/hr)",
            font=dict(
                size=11
            )
        )
    )

    annotation = go.layout.Annotation(
        x=current_time,
        y=0,
        xref="x",
        yref="y",
        text="evaluation point",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ayref="y",
        ay=-1.5
    )

    return axis, annotation


def prepare_loop_prediction(predicted_bg_dates, predicted_bg_values):
    bg_prediction_trace = go.Scattergl(
        name="predicted bg",
        x=predicted_bg_dates,
        y=predicted_bg_values,
        hoverinfo="y+name+x",
        mode='markers+lines',
        line=dict(
            color="#9886CF",
            dash="solid",
            width=0.5
        ),
        marker=dict(
            size=5,
        )
    )
    bg_prediction_trace.yaxis = "y2"

    return bg_prediction_trace


def prepare_loop_temp_basal(basal, current_time, recommended_temp_basal):
    if recommended_temp_basal is not None:
        rec_temp_basal_rate = recommended_temp_basal[0]
        rec_temp_basal_duration = recommended_temp_basal[1]
    else:
        rec_temp_basal_rate = basal.loc[basal.index.max(), "basal_rate_values"]
        rec_temp_basal_duration = 30

    rec_basal_trace = go.Scatter(
        name="temp basal set = {} U/hr".format(rec_temp_basal_rate),
        mode='lines',
        x=[
           current_time,
           current_time + datetime.timedelta(minutes=rec_temp_basal_duration),
        ],
        y=[rec_temp_basal_rate, rec_temp_basal_rate],
        hoverinfo="y+name+x",
        line=dict(
            shape='vh',
            color='#5691F0',
            dash='solid'
        ),
        fill='tozeroy',
    )

    rec_basal_trace.yaxis = "y"

    return rec_basal_trace


def prepare_loop_bolus(recommended_bolus, current_time):

    df_trace = go.Scatter(
        name="recommended bolus = {} U".format(recommended_bolus),
        showlegend=True,
        mode='markers',
        x=[current_time],
        y=[recommended_bolus+0.25],
        hoverinfo="text",
        hovertext=["{} rec bolus".format(recommended_bolus)],
        marker=dict(
            symbol='triangle-down-open',
            size=10 + recommended_bolus,
            color="#5691F0"
        ),
    )

    df_trace.yaxis = "y"

    return df_trace


def prepare_suspend(suspend_threshold, current_time):
    df_trace = go.Scatter(
        name="suspend threshold = {} mg/dL".format(suspend_threshold),
        mode='lines',
        x=[
           current_time - datetime.timedelta(days=1),
           current_time + datetime.timedelta(days=1),
        ],
        y=[suspend_threshold, suspend_threshold],
        hoverinfo="none",
        line=dict(
            shape='vh',
            color='#FA8E8E',
            dash='solid'
        ),
        opacity=0.25,
    )
    df_trace.yaxis = "y2"

    return df_trace


def prepare_insulin_effect_onboard_trace(
        inputs, dose_events, basal_rates, isf, continguous_ts
):
    if len(dose_events) > 0:
        # add basal rates to time series
        df = pd.merge(
            continguous_ts,
            basal_rates[["datetime", "basal_rate_values"]],
            on="datetime",
            how="left"
        )
        df["basal_rate_values"].fillna(method='ffill', inplace=True)

        df = pd.merge(
            df,
            isf[["sensitivity_ratio_start_times", "sensitivity_ratio_values"]],
            left_on="time",
            right_on="sensitivity_ratio_start_times",
            how="left"
        )

        df["sensitivity_ratio_values"].fillna(method='ffill', inplace=True)

        dose_data = pd.merge(
            dose_events,
            df,
            left_on="dose_start_times",
            right_on="datetime",
            how="left"
        )

        scheduled_basal_rates = list(dose_data["basal_rate_values"].values)

        (iob_dates, iob_values) = insulin_on_board(
            dose_types=inputs.get("dose_types"),
            start_dates=inputs.get("dose_start_times"),
            end_dates=inputs.get("dose_end_times"),
            values=inputs.get("dose_values"),
            scheduled_basal_rates=scheduled_basal_rates,
            model=inputs.get("settings_dictionary").get("model"),
            start=None,
            end=None,
            delay=10,
            delta=5
        )

        iob_df = pd.DataFrame(iob_dates, columns=["datetime"])
        iob_df["iob_values"] = iob_values

        # add isf time series
        iob_effect = pd.merge(
            iob_df,
            df,
            on="datetime",
            how="left"
        )

        iob_effect["values"] = (
            iob_effect["iob_values"] * iob_effect["sensitivity_ratio_values"]
        )

        df_trace = go.Scatter(
            name="iob potential",
            legendgroup="ob potential",
            visible="legendonly",
            mode='lines',
            x=iob_effect["datetime"],
            y=-iob_effect["values"],
            hoverinfo="name+x",
            line=dict(
                color='#5691F0',
                dash='solid'
            ),
            fill='tozeroy',
            fillcolor='rgba(86,145,240, 0.125)'
        )

    else:

        df_trace = go.Scatter(
            name="insulin effect on board",
            mode='lines',
            x=[],
            y=[],
            hoverinfo="y+name+x",
            line=dict(
                color='#5691F0',
                dash='solid'
            ),
            fill='tozeroy',
            fillcolor='rgba(86,145,240, 0.125)'
        )

    df_trace.yaxis = "y3"

    df_axis = dict(
            domain=[0.2875, 0.4875],
            fixedrange=True,
            hoverformat=".1f",
            zeroline=False,
            showgrid=True,
            gridcolor="#c0c0c0",
            title=dict(
                text="Relative<br>Effects (mg/dL)",
                font=dict(
                    size=11
                )
            )
        )

    return df_trace, df_axis


def prepare_carb_effect_onboard_trace(
        loop_output, carbs, isf, carb_ratios, continguous_ts
):
    df = pd.merge(
        continguous_ts,
        isf,
        left_on="time",
        right_on="sensitivity_ratio_start_times",
        how="left"
    )
    df["sensitivity_ratio_values"].fillna(method='ffill', inplace=True)

    df = pd.merge(
        df,
        carb_ratios,
        left_on="time",
        right_on="carb_ratio_start_times",
        how="left"
    )
    df["carb_ratio_values"].fillna(method='ffill', inplace=True)

    df["csf"] = df["sensitivity_ratio_values"] / df["carb_ratio_values"]

    settings_schedules = df[[
        "datetime",
        "sensitivity_ratio_values",
        "carb_ratio_values",
        "csf"
    ]].copy()

    settings_schedules.dropna(subset=['csf'], inplace=True)

    settings_schedules = pd.merge(
        create_contiguous_ts(
            settings_schedules["datetime"].min(),
            settings_schedules["datetime"].max(),
            freq="5min"
        ),
        settings_schedules,
        on="datetime",
        how="left"
    )

    if len(carbs) > 0:

        date_min = (
            carbs["datetime"].dt.round("5min").min() - pd.Timedelta("5min")
        )
        date_max = loop_output.get("cob_timeline_dates")[0] - pd.Timedelta("5min")
        carb_effect_ob = (
            create_contiguous_ts(date_min, date_max, freq="5min")
        )
        carb_effect_ob["cob"] = np.nan
        # TODO: there has to be a better way to get historical carbs on board
        # this method is re-running the loop algorithm
        for d in carb_effect_ob["datetime"]:
            inputs = loop_output.get("input_data").copy()
            inputs["time_to_calculate_at"] = (
                datetime.datetime.fromisoformat(d.isoformat())
            )
            temp_loop_output = update(inputs)
            carb_effect_ob.loc[carb_effect_ob["datetime"] == d, "cob"] = (
                temp_loop_output.get("carbs_on_board")
            )

        # get the carbs on board time series
        cob_df = pd.DataFrame()
        cob_df["datetime"] = loop_output.get("cob_timeline_dates")
        cob_df["cob"] = loop_output.get("cob_timeline_values")

        carb_effect_ob = pd.concat(
            [carb_effect_ob, cob_df], ignore_index=True, sort=True
        )

        carb_effect_ob = pd.merge(
            carb_effect_ob,
            df[["datetime", "csf"]],
            on="datetime",
            how="left"
        )

        carb_effect_ob["values"] = (
            carb_effect_ob["cob"] * carb_effect_ob["csf"]
        )

        carb_effect_ob_trace = go.Scatter(
            name="cob potential",
            legendgroup="ob potential",
            visible="legendonly",
            mode='lines',
            x=carb_effect_ob["datetime"],
            y=carb_effect_ob["values"],
            hoverinfo="name+x",
            line=dict(
                color='#0AA648',
                dash='solid'
            ),
            fill='tozeroy',
            fillcolor='rgba(10,166,72, 0.125)'
        )

    else:
        carb_effect_ob_trace = go.Scatter(
            name="carb effect on board",
            mode='lines',
            x=[],
            y=[],
            line=dict(
                color='#0AA648',
                dash='solid'
            ),
            fill='tozeroy',
            fillcolor='rgba(10,166,72, 0.125)'
        )

    carb_effect_ob_trace.yaxis = "y3"

    return carb_effect_ob_trace, settings_schedules


def prepare_all_effect_traces(loop_output):

    starting_date = loop_output.get("input_data").get("glucose_dates")[-1]
    starting_glucose = loop_output.get("input_data").get("glucose_values")[-1]

    predict_bg_df = pd.DataFrame(
        loop_output.get("predicted_glucose_dates"), columns=["datetime"]
    )
    predict_bg_df["values"] = loop_output.get("predicted_glucose_values")
    predict_bg_df["relValues"] = (
        predict_bg_df["values"] - predict_bg_df["values"].shift(1)
    ).fillna(0)

    predict_bg_effect_trace = go.Scatter(
        name="predicted bg (relative) effect",
        legendgroup="rel predictions",
        mode='markers+lines',
        x=predict_bg_df["datetime"],
        y=predict_bg_df["relValues"],
        hoverinfo="y+name+x",
        line=dict(
            color='#9886CF',
            dash='solid',
            width=0.25
        ),
        marker=dict(
            size=4,
        )
    )
    predict_bg_effect_trace.yaxis = "y3"

    insulin_predicted_glucose_dates, insulin_predicted_glucose_values = (
        predict_glucose(
            starting_date,
            starting_glucose,
            insulin_effect_dates=loop_output.get("insulin_effect_dates"),
            insulin_effect_values=loop_output.get("insulin_effect_values")
        )
    )

    insulin_df = pd.DataFrame(
        insulin_predicted_glucose_dates, columns=["datetime"]
    )
    insulin_df["values"] = insulin_predicted_glucose_values
    insulin_df["relValues"] = (
        insulin_df["values"] - insulin_df["values"].shift(1)
    ).fillna(0)

    insulin_effect_trace = go.Scatter(
        name="insulin effect",
        legendgroup="rel predictions",
        mode='markers+lines',
        x=insulin_df["datetime"],
        y=insulin_df["relValues"],
        hoverinfo="y+name+x",
        line=dict(
            color='#5691F0',
            dash='solid',
            width=0.25
        ),
        marker=dict(
            size=4,
        )
    )
    insulin_effect_trace.yaxis = "y3"

    carb_predicted_glucose_dates, carb_predicted_glucose_values = (
        predict_glucose(
            starting_date,
            starting_glucose,
            carb_effect_dates=loop_output.get("carb_effect_dates"),
            carb_effect_values=loop_output.get("carb_effect_values")
        )
    )

    carb_df = pd.DataFrame(
        carb_predicted_glucose_dates, columns=["datetime"]
    )
    carb_df["values"] = carb_predicted_glucose_values
    carb_df["relValues"] = (
        carb_df["values"] - carb_df["values"].shift(1)
    ).fillna(0)

    carb_effect_trace = go.Scatter(
        name="carb effect",
        legendgroup="rel predictions",
        mode='markers+lines',
        x=carb_df["datetime"],
        y=carb_df["relValues"],
        hoverinfo="y+name+x",
        line=dict(
            color='#0AA648',
            dash='solid',
            width=0.25
        ),
        marker=dict(
            size=4,
        )
    )
    carb_effect_trace.yaxis = "y3"

    momentum_predicted_glucose_dates, momentum_predicted_glucose_values = (
        predict_glucose(
            starting_date,
            starting_glucose,
            momentum_dates=loop_output.get("momentum_effect_dates"),
            momentum_values=loop_output.get("momentum_effect_values")
        )
    )

    momentum_indices = np.arange(0, len(momentum_predicted_glucose_values))

    if loop_output.get("retrospective_effect_dates"):
        rc_predicted_glucose_dates, rc_predicted_glucose_values = (
            predict_glucose(
                starting_date,
                starting_glucose,
                correction_effect_dates=(
                    loop_output.get("retrospective_effect_dates")
                ),
                correction_effect_values=(
                    loop_output.get("retrospective_effect_values")
                )
            )
        )

        rc_df = pd.DataFrame(rc_predicted_glucose_dates, columns=["datetime"])
        rc_df["values"] = rc_predicted_glucose_values
        rc_df["relValues"] = (
            rc_df["values"] - rc_df["values"].shift(1)
        ).fillna(0)

        rc_effect_trace = go.Scatter(
            name="rc effect",
            legendgroup="rel predictions",
            mode='markers+lines',
            x=rc_df["datetime"],
            y=rc_df["relValues"],
            hoverinfo="y+name+x",
            line=dict(
                color='#ED5393',
                dash='solid',
                width=0.25
            ),
            marker=dict(
                size=4,
            )
        )

        momentum_values = (
            predict_bg_df.loc[momentum_indices, "relValues"]
            - insulin_df.loc[momentum_indices, "relValues"]
            - carb_df.loc[momentum_indices, "relValues"]
            - rc_df.loc[momentum_indices, "relValues"]
        )

    else:
        rc_effect_trace = go.Scatter(
            name="rc effect",
            legendgroup="rel predictions",
            mode='markers+lines',
            x=[],
            y=[],
            hoverinfo="y+name+x",
            line=dict(
                color='#ED5393',
                dash='solid',
                width=0.25
            ),
            marker=dict(
                size=4,
            )
        )

        momentum_values = (
            predict_bg_df.loc[momentum_indices, "relValues"]
            - insulin_df.loc[momentum_indices, "relValues"]
            - carb_df.loc[momentum_indices, "relValues"]
        )

    rc_effect_trace.yaxis = "y3"

    momentum_effect_trace = go.Scatter(
        name="momentum effect",
        legendgroup="rel predictions",
        mode='markers+lines',
        x=momentum_predicted_glucose_dates,
        y=momentum_values,
        hoverinfo="y+name+x",
        line=dict(
            color='#CF7911',
            dash='solid',
            width=0.25
        ),
        marker=dict(
            size=4,
        )
    )
    momentum_effect_trace.yaxis = "y3"

    return (
        predict_bg_effect_trace, insulin_effect_trace, carb_effect_trace,
        momentum_effect_trace, rc_effect_trace
    )


def make_settings_traces(settings_schedules):
    isf_effect_trace = go.Scatter(
        name="isf (mg/dL/U)",
        mode='lines',
        x=settings_schedules["datetime"],
        y=settings_schedules["sensitivity_ratio_values"],
        hoverinfo="y+name+x",
        line=dict(
            color='#5691F0',
            dash='solid',
            width=0.75
        ),
    )
    isf_effect_trace.yaxis = "y4"

    cir_effect_trace = go.Scatter(
        name="cir (g/U)",
        mode='lines',
        x=settings_schedules["datetime"],
        y=settings_schedules["carb_ratio_values"],
        hoverinfo="y+name+x",
        line=dict(
            color='#0AA648',
            dash='solid',
            width=0.75
        ),
    )
    cir_effect_trace.yaxis = "y4"

    csf_effect_trace = go.Scatter(
        name="csf (mg/dL/g)",
        mode='lines',
        x=settings_schedules["datetime"],
        y=settings_schedules["csf"],
        hoverinfo="y+name+x",
        line=dict(
            color='#6483B4',
            dash='solid',
            width=0.75
        ),
    )
    csf_effect_trace.yaxis = "y4"

    settings_axis = dict(
            domain=[0.2125, 0.2625],
            fixedrange=True,
            hoverformat=".1f",
            zeroline=False,
            showgrid=True,
            gridcolor="#c0c0c0",
            title=dict(
                text="Sensitivity<br>Schedule",
                font=dict(
                    size=11
                )
            )
    )
    return isf_effect_trace, cir_effect_trace, csf_effect_trace, settings_axis


def prepare_layout(
    current_time, bg_axis, insulin_axis, effect_on_board_axis, settings_axis,
    top_annotation, bottom_annotation,
):
    layout = go.Layout(
        showlegend=True,
        plot_bgcolor="white",
        yaxis2=bg_axis,
        yaxis=insulin_axis,
        yaxis3=effect_on_board_axis,
        yaxis4=settings_axis,

        xaxis=dict(
            range=(
                current_time - datetime.timedelta(hours=8),
                current_time + datetime.timedelta(hours=6)
            ),
            showgrid=True,
            gridcolor="#c0c0c0",
            hoverformat="%H:%M"
        ),
        annotations=[
            top_annotation,
            bottom_annotation
        ],
        dragmode="pan",
        hovermode="x"
    )

    return layout


def make_scenario_figure(loop_output):
    inputs = loop_output.get("input_data")

    # convert dict_inputs_to_dataframes
    (
     basal_rates, carb_events, carb_ratios, dose_events, blood_glucose,
     df_last_temporary_basal, df_misc, df_sensitivity_ratio,
     df_settings, df_target_range
    ) = dict_inputs_to_dataframes(inputs)

    current_time = inputs.get("time_to_calculate_at")

    # %% blood glucose data
    bg_df, bg_trace, bg_axis, bg_annotation = (
        prepare_bg(blood_glucose, current_time)
    )

    # create a contiguous time series for the other data types
    date_min = bg_df["glucose_dates"].min() - datetime.timedelta(days=1)
    date_max = current_time + datetime.timedelta(days=1)
    continguous_ts = create_contiguous_ts(date_min, date_max)

    # correction range
    target_range, target_traces = (
        prepare_target_range(df_target_range, continguous_ts, current_time)
    )

    # suspend threshold
    suspend_threshold = inputs.get("settings_dictionary").get("suspend_threshold")
    suspend_trace = prepare_suspend(suspend_threshold, current_time)

    # %% insulin and carb data
    dose_events["type"] = (
        dose_events["dose_types"].apply(convert_times_and_types)
    )

    # basal data
    basal, sbr, basal_delivered_traces, scheduled_basal_traces,  = (
        prepare_basal(basal_rates, dose_events, continguous_ts, current_time)
    )

    # bolus data
    bolus, bolus_trace = prepare_bolus(dose_events)

    # carb data (cir and carb events)
    carbs, carb_trace = prepare_carbs(carb_events, carb_ratios, continguous_ts)

    # prepare insulin axis
    insulin_axis, insulin_annotation = (
        prepare_insulin_axis(basal, bolus, carbs, current_time)
    )

    # %% add loop prediction, temp basal, and bolus recommendation
    # loop prediction
    predicted_glucose_dates = loop_output.get("predicted_glucose_dates")
    predicted_glucose_values = loop_output.get("predicted_glucose_values")
    loop_prediction_trace = prepare_loop_prediction(
        predicted_glucose_dates, predicted_glucose_values
    )

    # recommended temp basal
    loop_temp_basal = loop_output.get("recommended_temp_basal")
    loop_basal_trace = (
        prepare_loop_temp_basal(basal, current_time, loop_temp_basal)
    )

    # recommended bolus
    loop_rec_bolus = loop_output.get("recommended_bolus")[0]
    loop_bolus_trace = prepare_loop_bolus(loop_rec_bolus, current_time)

    # insulin effect on-board trace
    insulin_effect_on_board_trace, effect_on_board_axis = (
        prepare_insulin_effect_onboard_trace(
            inputs, dose_events, sbr, df_sensitivity_ratio, continguous_ts
        )
    )

    # carb effect on-board trace
    carb_effect_on_board_trace, settings_schedules = (
        prepare_carb_effect_onboard_trace(
            loop_output, carbs, df_sensitivity_ratio,
            carb_ratios, continguous_ts
        )
    )

    # get effect traces
    (
     predict_bg_effect_trace, insulin_effect_trace, carb_effect_trace,
     momentum_effect_trace, rc_effect_trace
    ) = prepare_all_effect_traces(loop_output)

    # make a settings trace
    isf_effect_trace, cir_effect_trace, csf_effect_trace, settings_axis = (
            make_settings_traces(settings_schedules)
    )

    # %% make figure
    fig_layout = prepare_layout(
        current_time,
        bg_axis, insulin_axis, effect_on_board_axis, settings_axis,
        bg_annotation, insulin_annotation,
    )

    traces = []
    traces.extend([bg_trace, loop_prediction_trace])
    traces.extend(target_traces)
    traces.extend([
        suspend_trace, insulin_effect_on_board_trace,
        carb_effect_on_board_trace, predict_bg_effect_trace,
        insulin_effect_trace, carb_effect_trace,
        momentum_effect_trace, rc_effect_trace,
        isf_effect_trace, cir_effect_trace, csf_effect_trace,
        carb_trace, bolus_trace,

    ])
    traces.extend(scheduled_basal_traces)
    traces.extend(basal_delivered_traces)
    traces.extend([loop_basal_trace, loop_bolus_trace])

    fig = go.Figure(data=traces, layout=fig_layout)

    return fig


# %% view example scenario(s)
def view_example():
    # load in example scenario files
    cutom_scenario_files = [
        "custom-scenario-table-template-simple.csv",
        "custom-scenario-table-template-complex.csv",
        "custom-scenario-table-example-3.csv",
        "hypothetical-scenario-1.csv",
        "hypothetical-scenario-2.csv",
        "custom-scenario-varying-isf-correction-target.csv"
    ]
    path = os.path.join(".", "example_files")
    table_path_name = os.path.join(path, cutom_scenario_files[5])
    custom_table_df = pd.read_csv(table_path_name, index_col=0)
    inputs_from_file = input_table_to_dict(custom_table_df)
    loop_algorithm_output = update(inputs_from_file)
    plotly_fig = make_scenario_figure(loop_algorithm_output)
    plot(plotly_fig, filename=table_path_name+".html")


if __name__ == "__main__":
    view_example()
