#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 13:35:43 2019

@author: annaquinlan
"""
# pylint: disable=C0200, C0103, R0912
import os
import json

from datetime import datetime, time

from loop_data_manager import runner


def get_glucose_data(glucose_dict):
    """ Load glucose values from an issue report cached_glucose dictionary

    Arguments:
    glucose_dict -- dictionary containing cached glucose sample information

    Output:
    2 lists in (date, glucose_value) format
    """
    dates = [
        datetime.strptime(
            dict_.get("startDate"),
            "%Y-%m-%d %H:%M:%S %z"
        )
        for dict_ in glucose_dict
    ]

    glucose_values = [float(dict_.get("quantity")) for dict_ in glucose_dict]

    assert len(dates) == len(glucose_values),\
        "expected output shape to match"

    return (dates, glucose_values)


def get_cached_insulin_data(data):
    """ Load doses from an issue report cached_doses dictionary

    Arguments:
    data -- dictionary containing cached dose information

    Output:
    5 lists in (dose_type (basal/bolus/suspend), start_dates, end_dates,
                values (in units/insulin), scheduled_basal_rates) format
    """
    dose_types = [
        dict_.get("type")[17:]
        if dict_.get("type").startswith("LoopKit.DoseType.")
        else dict_.get("type") for dict_ in data
    ]
    start_dates = [
        datetime.strptime(
            dict_.get("startDate"),
            "%Y-%m-%d %H:%M:%S %z"
        )
        for dict_ in data
    ]
    end_dates = [
        datetime.strptime(
            dict_.get("endDate"),
            "%Y-%m-%d %H:%M:%S %z"
        )
        for dict_ in data
    ]
    values = [float(dict_.get("value")) for dict_ in data]

    scheduled_basal_rates = [
        float(dict_.get("scheduledBasalRate"))
        if dict_.get("scheduledBasalRate") != "nil"
        else 0
        for dict_ in data
    ]

    assert len(dose_types) == len(start_dates) == len(end_dates) ==\
        len(values) == len(scheduled_basal_rates),\
        "expected output shape to match"

    return (dose_types, start_dates, end_dates, values,
            scheduled_basal_rates)


def get_normalized_insulin_data(data):
    """ Load doses from an issue report get_normalized_doses dictionary

    Arguments:
    data -- dictionary containing cached dose information

    Output:
    5 lists in (dose_type (basal/bolus/suspend), start_dates, end_dates,
                values (in units/insulin), scheduled_basal_rates) format
    """
    dose_types = [
        dict_.get("type")[17:]
        if dict_.get("type").startswith("LoopKit.DoseType.")
        else dict_.get("type") for dict_ in data
    ]
    start_dates = [
        datetime.strptime(
            dict_.get("startDate"),
            "%Y-%m-%d %H:%M:%S %z"
        )
        for dict_ in data
    ]
    end_dates = [
        datetime.strptime(
            dict_.get("endDate"),
            "%Y-%m-%d %H:%M:%S %z"
        )
        for dict_ in data
    ]
    values = [float(dict_.get("value")) for dict_ in data]

    scheduled_basal_rates = [
        float(dict_.get("scheduledBasalRate")[:-5])
        if dict_.get("scheduledBasalRate") != "nil"
        else 0
        for dict_ in data
    ]

    assert len(dose_types) == len(start_dates) == len(end_dates) ==\
        len(values) == len(scheduled_basal_rates),\
        "expected output shape to match"

    return (dose_types, start_dates, end_dates, values,
            scheduled_basal_rates)


def get_carb_data(data):
    """ Load carb information from an issue report cached_carbs dictionary

    Arguments:
    data -- dictionary containing cached carb information

    Output:
    3 lists in (carb_values, carb_start_dates, carb_absorption_times)
    format
    """
    carb_values = [float(dict_.get("quantity")) for dict_ in data]
    start_dates = [
        datetime.strptime(
            dict_.get("startDate"),
            " %Y-%m-%d %H:%M:%S %z"
        )
        for dict_ in data
    ]
    absorption_times = [
        float(dict_.get("absorptionTime")) / 60
        if dict_.get("absorptionTime")
        else None for dict_ in data
    ]

    assert len(start_dates) == len(carb_values) == len(absorption_times),\
        "expected input shapes to match"
    return (start_dates, carb_values, absorption_times)


def seconds_to_time(seconds):
    """ Convert seconds since midnight into a datetime.time object """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return time(int(hours), int(minutes), int(seconds))


def get_starts_and_ends_from_seconds(seconds_list):
    """ Given a list of seconds since midnight,
        convert into start and end times
    """
    starts = [seconds_to_time(seconds) for seconds in seconds_list]
    ends = [value for value in starts]
    ends.append(ends.pop(0))

    assert len(starts) == len(ends), "expected output shapes to match"

    return (starts, ends)


def get_sensitivities(data):
    """ Load insulin sensitivity schedule
        from an issue report isf_schedule dictionary

    Arguments:
    data -- dictionary containing ISF information

    Output:
    3 lists in (sensitivity_start_time, sensitivity_end_time,
                sensitivity_value (mg/dL/U)) format
    """
    seconds = [float(dict_.get("startTime")) for dict_ in data]

    (start_times, end_times) = get_starts_and_ends_from_seconds(seconds)

    values = [dict_.get("value") for dict_ in data]

    assert len(start_times) == len(end_times) == len(values),\
        "expected output shape to match"

    return (start_times, end_times, values)


def get_carb_ratios(data):
    """ Load carb ratio schedule
        from an issue report carb_ratio_schedule dictionary

    Arguments:
    data -- dictionary containing CR information

    Output:
    2 lists in (ratio_start_time, ratio_value (g/U)) format
    """
    seconds = [float(dict_.get("startTime")) for dict_ in data]

    start_times = get_starts_and_ends_from_seconds(seconds)[0]

    values = [dict_.get("value") for dict_ in data]

    assert len(start_times) == len(values),\
        "expected output shape to match"

    return (start_times, values)


def get_basal_schedule(data):
    """ Load basal rate schedule
        from an issue report basal_rate_schedule dictionary

    Arguments:
    data -- dictionary containing CR information

    Output:
    3 lists in (rate_start_time, rate_length (minutes), rate (U/hr)) format
    """
    seconds = [float(dict_.get("startTime")) for dict_ in data]
    rate_minutes = []
    for i in range(0, len(seconds)):
        if i == len(seconds) - 1:
            rate_minutes.append(
                (seconds[i] - seconds[0]) / 60
            )
        else:
            rate_minutes.append(
                (seconds[i+1] - seconds[i]) / 60
            )

    start_times = get_starts_and_ends_from_seconds(seconds)[0]

    values = [dict_.get("value") for dict_ in data]

    assert len(start_times) == len(rate_minutes) == len(values),\
        "expected output shapes to match"

    return (start_times, rate_minutes, values)


def get_settings(data):
    """ Load needed settings from an issue report

    Arguments:
    data -- the parsed issue report dictionary

    Output:
    Dictionary of settings
    """
    settings = {}

    model = data.get("insulin_model")
    if not model:
        raise RuntimeError("No insulin model information found")

    if model.lower() == "humalognovologchild":
        settings["model"] = [
            data.get("insulin_action_duration") / 60,
            65
        ]
    elif model.lower() == "humalognovologadult":
        settings["model"] = [
            data.get("insulin_action_duration") / 60,
            75
        ]
    elif model.lower() == "fiasp":
        settings["model"] = [
            data.get("insulin_action_duration") / 60,
            55
        ]
    else:  # Walsh model
        settings["model"] = [
            data.get("insulin_action_duration") / 60 / 60
        ]

    return settings


def parse_json(path, name):
    """ Get relevent information from a Loop issue report and use it to
        run PyLoopKit
    """
    data_path_and_name = os.path.join(path, name)

    issue_dict = json.load(
        open(data_path_and_name, "r")
    )

    if issue_dict.get("cached_glucose_samples"):
        glucose_data = get_glucose_data(
            issue_dict.get("cached_glucose_samples")
        )
    else:
        raise RuntimeError("No glucose information found")

    if issue_dict.get("cached_dose_entries"):
        dose_data = get_cached_insulin_data(
            issue_dict.get("cached_dose_entries")
        )
    elif issue_dict.get("get_normalized_dose_entries"):
        dose_data = get_normalized_insulin_data(
            issue_dict.get("get_normalized_dose_entries")
        )
    else:
        raise RuntimeError("No insulin dose information found")

    if issue_dict.get("cached_carb_entries"):
        carb_data = get_carb_data(
            issue_dict.get("cached_carb_entries")
        )
    else:
        carb_data = ([], [], [])

    settings = get_settings(issue_dict)

    if issue_dict.get("insulin_sensitivity_factor_schedule"):
        sensitivity_schedule = get_sensitivities(
            issue_dict.get("insulin_sensitivity_factor_schedule")
        )
    else:
        raise RuntimeError("No insulin sensitivity information found")

    if issue_dict.get("carb_ratio_schedule"):
        carb_ratio_schedule = get_carb_ratios(
            issue_dict.get("carb_ratio_schedule")
        )
    else:
        raise RuntimeError("No carb ratio information found")

    if issue_dict.get("basal_rate_schedule"):
        basal_schedule = get_basal_schedule(
            issue_dict.get("basal_rate_schedule")
        )
    else:
        raise RuntimeError("No basal rate information found")

    if issue_dict.get("recommended_temp_basal"):
        time_to_run = datetime.strptime(
            issue_dict.get("recommended_temp_basal").get("date") or
            issue_dict.get("recommended_temp_basal").get(" date"),
            "%Y-%m-%d %H:%M:%S %z"
        )
    elif issue_dict.get("recommended_bolus"):
        time_to_run = datetime.strptime(
            issue_dict.get("recommended_bolus").get("date") or
            issue_dict.get("recommended_bolus").get(" date"),
            "%Y-%m-%d %H:%M:%S %z"
        )
    else:
        raise RuntimeError("No information found about report time")

    runner(glucose_data,
           dose_data,
           carb_data,
           settings,
           sensitivity_schedule,
           carb_ratio_schedule,
           basal_schedule,
           time_to_run
           )


file_path = str(input("Path: "))
file_name = str(input("File name: ")) + ".json"

parse_json(file_path, file_name)
