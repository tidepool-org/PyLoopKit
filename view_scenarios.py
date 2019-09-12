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
from input_data_tools import input_table_to_dict, dict_inputs_to_dataframes
from loop_data_manager import update
import plotly.graph_objs as go
from plotly.offline import plot


# %% functions
def get_bg_colors(df):
    df['bg_colors'] = 'mediumaquamarine'
    df.loc[df['glucose_values'] < 54, 'bg_colors'] = 'indianred'
    low_location = (df['glucose_values'] > 54) & (df['glucose_values'] < 70)
    df.loc[low_location, 'bg_colors'] = 'lightcoral'
    high_location = (
        (df['glucose_values'] > 180) & (df['glucose_values'] <= 250)
    )
    df.loc[high_location, 'bg_colors'] = 'mediumpurple'
    df.loc[(df['glucose_values'] > 250), 'bg_colors'] = 'slateblue'

    return df


def prepare_bg(df):
    df = get_bg_colors(df)

    df_trace = go.Scattergl(
        name="bg",
        x=df["glucose_dates"],
        y=df["glucose_values"],
        hoverinfo="y+name",
        mode='markers',
        marker=dict(
            size=6,
            line=dict(width=0),
            color=df["bg_colors"]
        )
    )

    df_axis = dict(
            domain=[0.4, 1],
            range=[0, 400],
            tickvals=[-100, 40, 70, 180, 250, 400],
            fixedrange=True,
            hoverformat=".0f",
            zeroline=False,
            showgrid=True,
            gridcolor="#c0c0c0",
            title=dict(
                text="Blood Glucose (mg/dL)",
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
        text="current time",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ayref="y2",
        ay=425
    )

    df_trace.yaxis = "y2"

    return df, df_trace, df_axis, df_annotations


def create_contiguous_ts(date_min, date_max):
    date_range = pd.date_range(
        date_min,
        date_max,
        freq="1s"
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


def prepare_basal(basal_rates, df_dose, contig_ts):

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
    if (("basal" in unique_dose_types) | ("suspend" in unique_dose_types)):
        temp_basal = (
            df_dose[
                ((df_dose["type"] == "basal") | (df_dose["type"] == "suspend"))
            ].copy()
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

    # downsample
    df = downsample(df, current_time, freq="5min")

    sbr_trace = go.Scattergl(
        name="scheduled basal rate",
        mode='lines',
        x=df["datetime"],
        y=df["basal_rate_values"],
        hoverinfo="y+name",
        line=dict(
            shape='vh',
            color='lightskyblue',
            dash='dot'
        )
    )

    basal_trace = go.Scatter(
        name="basal delivered",
        mode='lines',
        x=df["datetime"],
        y=df["delivered"],
        hoverinfo="y+name",
        line=dict(
            shape='vh',
            color='lightskyblue'
        ),
        fill='tonexty'
    )

    sbr_trace.yaxis = "y"
    basal_trace.yaxis = "y"

    return df, sbr_trace, basal_trace


def prepare_bolus(df_dose):
    unique_dose_types = df_dose["type"].unique()
    if "bolus" in unique_dose_types:
        df = df_dose[df_dose["type"] == "bolus"]

        df_trace = go.Bar(
            name="bolus",
            x=df["dose_start_times"],
            y=df["dose_values"],
            hoverinfo="y+name",
            width=2000*60*10,
            marker=dict(color='cornflowerblue'),
            opacity=0.5
        )
    else:
        df_trace = []

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
        name="carbs",
        mode='markers + text',
        x=carb_df["datetime"],
        y=carb_df["bolus_height"] + 0.5,
        hoverinfo="name",
        marker=dict(
            color='gold',
            size=25
        ),
        text=carb_df["carb_values"],
        textposition='middle center'
    )

    df_trace.yaxis = "y"

    return carb_df, df_trace


def prepare_target_range(df_target_range, continguous_ts):
    df = pd.merge(
        continguous_ts,
        df_target_range,
        left_on="time",
        right_on="target_range_start_times",
        how="left"
    )
    df["target_range_minimum_values"].fillna(method='ffill', inplace=True)
    df["target_range_maximum_values"].fillna(method='ffill', inplace=True)
    df.dropna(subset=['target_range_minimum_values'], inplace=True)

    # downsample
    df = downsample(df, current_time, freq="5min")

    trace_top = go.Scatter(
        name="target range",
        mode='lines',
        x=df["datetime"],
        y=df["target_range_maximum_values"],
        hoverinfo="y+name",
        line=dict(
            shape='vh',
            color='lightskyblue',
            width=5
        ),
        opacity=0.125
    )

    trace_bottom = go.Scatter(
        showlegend=False,
        name="target range",
        mode='lines',
        x=df["datetime"],
        y=df["target_range_minimum_values"],
        hoverinfo="y+name",
        line=dict(
            shape='vh',
            color='lightskyblue',
            width=5
        ),
        opacity=0.125
    )

    trace_top.yaxis = "y2"
    trace_bottom.yaxis = "y2"

    return df, trace_top, trace_bottom


def prepare_insulin_axis(basal, bolus, carbs):

    axis = dict(
        domain=[0, 0.3],
        range=[0, max(
            basal["basal_rate_values"].max() + 1,
            basal["tbr"].max() + 1,
            carbs["bolus_height"].max() + 2,
            bolus["dose_values"].max() + 2,
        )],
        fixedrange=True,
        hoverformat=".2f",
        showgrid=True,
        gridcolor="#c0c0c0",
        title=dict(
            text="Insulin (U, U/hr)",
            font=dict(
                size=12
            )
        )
    )

    annotation = go.layout.Annotation(
        x=current_time,
        y=0,
        xref="x",
        yref="y",
        text="current time",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ayref="y",
        ay=-1.5
    )
    return axis, annotation


def prepare_layout(
    current_time, top_axis, bottom_axis, top_annotation, bottom_annotation
):
    layout = go.Layout(
        showlegend=True,
        plot_bgcolor="white",
        yaxis=bottom_axis,
        yaxis2=top_axis,
        xaxis=dict(
            range=(
                current_time - datetime.timedelta(hours=8),
                current_time + datetime.timedelta(hours=4)
            ),
            showgrid=True,
            gridcolor="#c0c0c0",
        ),
        annotations=[
            top_annotation,
            bottom_annotation
        ],
        dragmode="pan",
        hovermode="x"
    )
    return layout


# %% view the scenario
# load in example scenario files
cutom_scenario_files = [
    "custom-scenario-table-template-simple.csv",
    "custom-scenario-table-template-complex.csv",
]
path = os.path.join(".", "example_files")
table_path_name = os.path.join(path, cutom_scenario_files[0])
custom_table_df = pd.read_csv(table_path_name, index_col=0)
inputs = input_table_to_dict(custom_table_df)
# first make sure that the scenario runs
# getting no errors on run is a good sign
loop_output = update(inputs)

# convert dict_inputs_to_dataframes
(
 basal_rates, carb_events, carb_ratios, dose_events, bg_df,
 df_last_temporary_basal, df_misc, df_sensitivity_ratio,
 df_settings, df_target_range
) = dict_inputs_to_dataframes(inputs)

current_time = inputs.get("time_to_calculate_at")


# %% blood glucose data
bg_df, bg_trace, bg_axis, bg_annotation = prepare_bg(bg_df.copy())

# create a contiguous time series for the other data types
date_min = bg_df["glucose_dates"].min() - datetime.timedelta(days=1)
continguous_ts = create_contiguous_ts(date_min, current_time)

# get target range
target_range, target_trace_top, target_trace_bottom = (
    prepare_target_range(df_target_range, continguous_ts)
)


# %% insulin and carb data
dose_events["type"] = dose_events["dose_types"].apply(convert_times_and_types)

# bolus data
bolus, bolus_trace = prepare_bolus(dose_events)

# basal data
basal, scheduled_basal_trace, basal_delivered_trace = (
    prepare_basal(basal_rates, dose_events, continguous_ts)
)

# carb data (cir and carb events)
carbs, carb_trace = prepare_carbs(carb_events, carb_ratios, continguous_ts)

# prepare insulin axis
insulin_axis, insulin_annotation = prepare_insulin_axis(basal, bolus, carbs)


# %% make figure
fig_layout = prepare_layout(
    current_time, bg_axis, insulin_axis, bg_annotation, insulin_annotation
)

traces = [
    basal_delivered_trace, scheduled_basal_trace, bolus_trace,
    carb_trace, target_trace_top, target_trace_bottom, bg_trace
]
fig = go.Figure(data=traces, layout=fig_layout)
plot(fig)
