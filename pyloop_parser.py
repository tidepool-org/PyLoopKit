#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 13:35:43 2019

@author: annaquinlan
"""
# pylint: disable=C0200, C0103, R0912
import json
import numpy
import os

from datetime import datetime, time, timedelta

from loop_data_manager import runner


def get_glucose_data(glucose_dict, offset=0):
    """ Load glucose values from an issue report cached_glucose dictionary

    Arguments:
    glucose_dict -- dictionary containing cached glucose sample information
    offset -- the offset from UTC in seconds

    Output:
    2 lists in (date, glucose_value) format
    """
    dates = [
        datetime.strptime(
            dict_.get("startDate"),
            "%Y-%m-%d %H:%M:%S %z"
        ) + timedelta(seconds=offset)
        for dict_ in glucose_dict
    ]

    glucose_values = [float(dict_.get("quantity")) for dict_ in glucose_dict]

    assert len(dates) == len(glucose_values),\
        "expected output shape to match"

    return (dates, glucose_values)


def convert_to_correct_units(type_, start, end, value):
    """ Take a dose and convert it into the appropriate unit
        (either U or U/hr)
    """
    if type_.lower() == "bolus":
        return value
    else:
        return value / ((end - start).total_seconds()/60/60)


def get_insulin_data(
        data, offset=0, convert_to_units=False, entry_to_add=None):
    """ Load doses from an issue report cached_doses
        or normalized_insulin_doses dictionary

    Arguments:
    data -- dictionary containing cached dose information
    offset -- the offset from UTC in seconds
    convert_to_units -- convert from dose amounts to doses with the correct
                        units (so U for boluses and U/hr for basals)
    entry_to_add -- the last entry to add; this is normally used when getting
                    data from the "get_normalized_pump_event_dose" dictionary,
                    as it sometimes lacks the last insulin dose. This function
                    assumes that if it is a basal, it will need to be converted
                    to U/hr.

    Output:
    4 lists in (dose_type (basal/bolus/suspend), start_dates, end_dates,
                values (in units/insulin)) format
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
        ) + timedelta(seconds=offset)
        for dict_ in data
    ]
    end_dates = [
        datetime.strptime(
            dict_.get("endDate"),
            "%Y-%m-%d %H:%M:%S %z"
        ) + timedelta(seconds=offset)
        for dict_ in data
    ]
    values = []
    for i in range(0, len(data)):
        values.append(
            convert_to_correct_units(
                dose_types[i],
                start_dates[i],
                end_dates[i],
                float(data[i].get("value"))
            ) if convert_to_units else float(data[i].get("value"))
        )
    if entry_to_add:
        start = datetime.strptime(
            entry_to_add.get("startDate"),
            "%Y-%m-%d %H:%M:%S %z"
        ) + timedelta(seconds=offset)
        end = datetime.strptime(
            entry_to_add.get("endDate"),
            "%Y-%m-%d %H:%M:%S %z"
        ) + timedelta(seconds=offset)

        # if this entry is truly a new entry, convert to the appropriate units
        # and add to the output
        if not start == start_dates[-1] and not end == end_dates[-1]:
            dose_types.append(
                entry_to_add.get("type")[17:]
                if entry_to_add.get("type").startswith("LoopKit.DoseType.")
                else entry_to_add.get("type")
            )
            start_dates.append(start)
            end_dates.append(end)
            values.append(
                convert_to_correct_units(
                    dose_types[-1],
                    start,
                    end,
                    float(entry_to_add.get("value"))
                )
            )

    assert len(dose_types) == len(start_dates) == len(end_dates) ==\
        len(values),\
        "expected output shape to match"

    return (dose_types, start_dates, end_dates, values)


def get_carb_data(data, offset=0):
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
        ) + timedelta(seconds=offset)
        for dict_ in data
    ]
    absorption_times = [
        float(dict_.get("absorptionTime")) / 60
        if dict_.get("absorptionTime") is not None
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

    return (start_times, values, rate_minutes)


def get_target_range_schedule(data):
    """ Load target range schedule
        from an issue report "correction_range_schedule" dictionary
    """
    seconds = [float(dict_.get("startTime")) for dict_ in data]
    (start_times, end_times) = get_starts_and_ends_from_seconds(seconds)
    min_values = [float(dict_.get("value")[0]) for dict_ in data]
    max_values = [float(dict_.get("value")[1]) for dict_ in data]

    return (start_times, end_times, min_values, max_values)


def load_momentum_effects(data, offset=0):
    """ Load glucose momentum effects from a list """
    start_times = [
        datetime.strptime(
            dict_.get("startDate"),
            "%Y-%m-%d %H:%M:%S %z"
        )
        for dict_ in data
    ]
    values = [
        float(dict_.get("quantity")) for dict_ in data
    ]
    return (start_times, values)


def get_counteractions(data, offset=0):
    """ Load counteraction effect data from a list """
    start_times = [
        datetime.strptime(
            dict_.get("start_time"),
            "%Y-%m-%d %H:%M:%S %z"
        )
        for dict_ in data
    ]
    end_times = [
        datetime.strptime(
            dict_.get("end_time"),
            " %Y-%m-%d %H:%M:%S %z"
        )
        for dict_ in data
    ]
    values = [
        float(dict_.get("value")) for dict_ in data
    ]
    return (start_times, end_times, values)


def load_insulin_effects(data, offset=0):
    """ Load insulin effect data from a list """
    start_times = [
        datetime.strptime(
            dict_.get("start_time"),
            "%Y-%m-%d %H:%M:%S %z"
        )
        for dict_ in data
    ]
    values = [
        float(dict_.get("value")) for dict_ in data
    ]
    return (start_times, values)


def get_retrospective_effects(data, offset=0):
    """ Load retrospective effect data from a list """
    start_times = [
        datetime.strptime(
            dict_.get("startDate"),
            "%Y-%m-%d %H:%M:%S %z"
        )
        for dict_ in data
    ]
    values = [
        float(dict_.get("quantity")) for dict_ in data
    ]
    return (start_times, values)


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

    momentum_interval = data.get("glucose_store").get("momentumDataInterval")
    if momentum_interval is not None:
        settings["momentum_time_interval"] = float(momentum_interval) / 60
    else:
        settings["momentum_time_interval"] = 15

    suspend_threshold = data.get("suspend_threshold")
    if suspend_threshold is not None:
        settings["suspend_threshold"] = float(suspend_threshold)
    else:
        print("No suspend threshold set")
        settings["suspend_threshold"] = None

    settings["dynamic_carb_absorption_enabled"] = True
    settings["retrospective_correction_integration_interval"] = 30
    settings["recency_interval"] = 15
    settings["retrospective_correction_grouping_interval"] = 30
    settings["rate_rounder"] = 0.05
    settings["delay"] = 10

    settings["default_absorption_times"] = [
         float(data.get("carb_default_absorption_times_fast")) / 60,
         float(data.get("carb_default_absorption_times_medium")) / 60,
         float(data.get("carb_default_absorption_times_slow")) / 60
         ]

    settings["max_basal_rate"] = data.get("maximum_basal_rate")
    settings["max_bolus"] = data.get("maximum_bolus")
    settings["retrospective_correction_enabled"] = True if data.get(
        "retrospective_correction_enabled"
    ) and data.get(
        "retrospective_correction_enabled"
    ).lower() == "true" else False

    return settings


def get_last_temp_basal(data, offset=0):
    """ Load the last temporary basal from an issue report
        "last_temp_basal" dictionary
    """
    if (data.get(" type") == "LoopKit.DoseType.tempBasal"
        or data.get("type") == "LoopKit.DoseType.tempBasal"
       ):
        type_ = "tempBasal"
    elif (data.get(" type") == "LoopKit.DoseType.basal"
          or data.get("type") == "LoopKit.DoseType.basal"
        ):
        type_ = "basal"
    else:
        raise RuntimeError("The last temporary basal is not a basal")

    return [
        type_,
        datetime.strptime(
            data.get(" startDate") if data.get(" startDate") is not None
            else data.get("startDate"),
            "%Y-%m-%d %H:%M:%S %z"
        ) + timedelta(seconds=offset),
        datetime.strptime(
            data.get(" endDate") if data.get(" endDate") is not None
            else data.get("endDate"),
            "%Y-%m-%d %H:%M:%S %z"
        ) + timedelta(seconds=offset),
        float(data.get(" value")) if data.get(" value") is not None
        else float(data.get("value"))
    ]


def sort_by_first_list(list_1, list_2, list_3=None, list_4=None, list_5=None):
    """ Sort lists that are matched index-wise, using the first list as the
        property to sort by

    Example:
        l1: [50, 2, 3]               ->     [2, 3, 50]
        l2: [dog, cat, parrot]       ->     [cat, parrot, dog]
    """
    unsort_1 = numpy.array(list_1)
    unsort_2 = numpy.array(list_2)
    unsort_3 = numpy.array(list_3)
    unsort_4 = numpy.array(list_4)
    unsort_5 = numpy.array(list_5)

    sort_indexes = unsort_1.argsort()

    unsort_1.sort()
    list_1 = list(unsort_1)
    l2 = list(unsort_2[sort_indexes])
    if list_3:
        l3 = list(unsort_3[sort_indexes])
    else:
        l3 = []
    if list_4:
        l4 = list(unsort_4[sort_indexes])
    else:
        l4 = []
    if list_5:
        l5 = list(unsort_5[sort_indexes])
    else:
        l5 = []

    return (list_1, l2, l3, l4, l5)


def sort_dose_lists(list_1, list_2, list_3=None, list_4=None, list_5=None):
    """ Sort dose lists that are matched index-wise, using the *second* list as
         the property to sort by

    Example:
        l1: [50, 2, 3]               ->     [2, 3, 50]
        l2: [dog, cat, parrot]       ->     [cat, parrot, dog]
    """
    unsort_1 = numpy.array(list_1)
    unsort_2 = numpy.array(list_2)
    unsort_3 = numpy.array(list_3)
    unsort_4 = numpy.array(list_4)
    unsort_5 = numpy.array(list_5)

    sort_indexes = unsort_2.argsort()

    l1 = list(unsort_1[sort_indexes])
    unsort_2.sort()
    list_2 = list(unsort_2)
    if list_3:
        l3 = list(unsort_3[sort_indexes])
    else:
        l3 = []
    if list_4:
        l4 = list(unsort_4[sort_indexes])
    else:
        l4 = []
    if list_5:
        l5 = list(unsort_5[sort_indexes])
    else:
        l5 = []

    return (l1, list_2, l3, l4, l5)


def remove_too_new_values(
        sort_time,
        list_1, list_2, list_3=None, list_4=None, list_5=None,
        is_dose_data=False
        ):
    """ Remove values that occur after a certain date. This function makes the
        assumption that the date list is sorted in ascending order, and
        that all lists (if they are not None) are the same length. The first
        list must be the list with the times, unless is_dose_data is True,
        in which case the second list must contain the times.

    Arguments:
    sort_time -- the datetime after which to remove values
    """
    l1 = []
    l2 = []
    l3 = []
    l4 = []
    l5 = []

    for i in range(0, len(list_1)):
        # if this isn't dose data, use the first list to sort
        if not is_dose_data and list_1[i] <= sort_time:
            l1.append(list_1[i])
            l2.append(list_2[i])
            if list_3:
                l3.append(list_3[i])
            if list_4:
                l4.append(list_4[i])
            if list_5:
                l5.append(list_5[i])
        # otherwise, use the second list to sort
        elif is_dose_data and list_2[i] <= sort_time:
            l1.append(list_1[i])
            l2.append(list_2[i])
            if list_3:
                l3.append(list_3[i])
            if list_4:
                l4.append(list_4[i])
            if list_5:
                l5.append(list_5[i])

    return (l1, l2, l3, l4, l5)


def parse_report_and_run(path, name):
    """ Get relevent information from a Loop issue report and use it to
        run PyLoopKit
    """
    data_path_and_name = os.path.join(path, name)

    issue_dict = json.load(
        open(data_path_and_name, "r")
    )

    if issue_dict.get("basal_rate_timeZone") is not None:
        offset = issue_dict.get("basal_rate_timeZone")
    elif issue_dict.get("carb_ratio_timeZone") is not None:
        offset = issue_dict.get("carb_ratio_timeZone")
    elif issue_dict.get("insulin_sensitivity_factor_timeZone") is not None:
        offset = issue_dict.get("insulin_sensitivity_factor_timeZone")
    else:
        offset = 0

    if issue_dict.get("recommended_temp_basal"):
        time_to_run = datetime.strptime(
            issue_dict.get("recommended_temp_basal").get("date") or
            issue_dict.get("recommended_temp_basal").get(" date"),
            "%Y-%m-%d %H:%M:%S %z"
        ) + timedelta(seconds=offset)
    elif issue_dict.get("recommended_bolus"):
        time_to_run = datetime.strptime(
            issue_dict.get("recommended_bolus").get("date") or
            issue_dict.get("recommended_bolus").get(" date"),
            "%Y-%m-%d %H:%M:%S %z"
        ) + timedelta(seconds=offset)
    else:
        raise RuntimeError("No information found about report time")

    if issue_dict.get("cached_glucose_samples"):
        glucose_data = get_glucose_data(
            issue_dict.get("cached_glucose_samples"),
            offset
        )
        glucose_data = remove_too_new_values(
            time_to_run,
            *sort_by_first_list(
                *glucose_data
            )[0:2]
        )[0:2]

    else:
        raise RuntimeError("No glucose information found")

    if (issue_dict.get("get_normalized_pump_event_dose")
            and issue_dict.get("get_normalized_dose_entries")):
        dose_data = get_insulin_data(
            issue_dict.get("get_normalized_pump_event_dose"),
            offset,
            entry_to_add=issue_dict.get("get_normalized_dose_entries")[-1]
        )
    elif issue_dict.get("get_normalized_dose_entries"):
        dose_data = get_insulin_data(
            issue_dict.get("get_normalized_dose_entries"),
            offset,
            convert_to_units=True
        )
    elif issue_dict.get("cached_dose_entries"):
        dose_data = get_insulin_data(
            issue_dict.get("cached_dose_entries"),
            offset,
            convert_to_units=True
        )
    else:
        print("No insulin dose information found")
        dose_data = ([], [], [], [])
    dose_data = remove_too_new_values(
        time_to_run,
        *sort_dose_lists(*dose_data)[0:4],
        is_dose_data=True
    )[0:4]

    if issue_dict.get("cached_carb_entries"):
        carb_data = get_carb_data(
            issue_dict.get("cached_carb_entries"),
            offset,
        )
        carb_data = sort_by_first_list(*carb_data)[0:3]
    else:
        carb_data = ([], [], [])

    settings = get_settings(issue_dict)

    if issue_dict.get("insulin_sensitivity_factor_schedule"):
        sensitivity_schedule = get_sensitivities(
            issue_dict.get("insulin_sensitivity_factor_schedule")
        )
        sensitivity_schedule = sort_by_first_list(*sensitivity_schedule)[0:3]
    else:
        raise RuntimeError("No insulin sensitivity information found")

    if issue_dict.get("carb_ratio_schedule"):
        carb_ratio_schedule = get_carb_ratios(
            issue_dict.get("carb_ratio_schedule")
        )
        carb_ratio_schedule = sort_by_first_list(*carb_ratio_schedule)[0:2]
    else:
        raise RuntimeError("No carb ratio information found")

    if issue_dict.get("basal_rate_schedule"):
        basal_schedule = get_basal_schedule(
            issue_dict.get("basal_rate_schedule")
        )
        basal_schedule = sort_by_first_list(*basal_schedule)[0:3]
    else:
        raise RuntimeError("No basal rate information found")

    if issue_dict.get("correction_range_schedule"):
        target_range_schedule = get_target_range_schedule(
            issue_dict.get("correction_range_schedule")
        )
        target_range_schedule = sort_by_first_list(*target_range_schedule)[0:4]
    else:
        raise RuntimeError("No target range rate information found")

    if issue_dict.get("last_temp_basal"):
        last_temp_basal = get_last_temp_basal(
            issue_dict.get("last_temp_basal"), offset
        )
    else:
        last_temp_basal = []
        print("No information found about the last temporary basal rate")

    test_counteraction = get_counteractions(
        issue_dict.get("insulin_counteraction_effects"), offset
    )
    '''counteraction_effect = counteraction_effects(
        *glucose_data,
        [False for i in glucose_data[0]],
        ["PyLoop" for i in glucose_data[0]],
        *test_effects
        )

    recommendations = runner(
        glucose_data,
        dose_data,
        carb_data,
        settings,
        sensitivity_schedule,
        carb_ratio_schedule,
        basal_schedule,
        target_range_schedule,
        last_temp_basal,
        time_to_run,
        counteraction_starts=test_counteraction[0],
        counteraction_ends=test_counteraction[1],
        counteraction_values=test_counteraction[2],
        actual_effect_starts=test_effects[0],
        actual_effect_ends=test_effects[1]
        )


file_path = str(input("Path: "))
file_name = str(input("File name: ")) + ".json"

parse_report_and_run(file_path, file_name)
