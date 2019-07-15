#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 18:04:24 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/Loop/blob/
8c1dfdba38fbf6588b07cee995a8b28fcf80ef69/Loop/Managers/LoopDataManager.swift
"""
# pylint: disable=R0913, R0914, C0200, R1705, R0912
from datetime import timedelta
import sys

from insulin_math import is_time_between, find_ratio_at_time
from date import time_interval_since
from walsh_insulin_model import walsh_percent_effect_remaining
from exponential_insulin_model import percent_effect_remaining


def filter_date_range_for_doses(
        types, starts, ends, values, scheduled_basals,
        start_date,
        end_date
        ):
    """ Returns an array of elements filtered by the specified date range.

    Arguments:
    types -- String of type of dose (basal, bolus, etc)
    starts -- start dates (datetime)
    ends -- end dates (datetime)
    values -- glucose values
    scheduled_basals -- scheduled basal rate during dose

    start_date -- the earliest date of elements to return
    end_date -- the last date of elements to return

    Output:
    Filtered dates in format (starts, ends, values)
    """
    # ends might not necesarily be the same length as starts/values
    # because not all types have "end dates"
    assert len(types) == len(starts) == len(values) == len(scheduled_basals),\
        "expected input shapes to match"

    (filtered_types,
     filtered_starts,
     filtered_ends,
     filtered_values,
     filtered_scheduled_basals
     ) = ([], [], [], [], [])

    for i in range(0, len(starts)):
        if start_date and ends and ends[i] < start_date:
            continue

        if start_date and not ends and starts[i] < start_date:
            continue

        if end_date and starts[i] > end_date:
            continue

        filtered_types.append(types[i])
        filtered_starts.append(starts[i])
        filtered_ends.append(ends[i] if ends else None)
        filtered_values.append(values[i])
        filtered_scheduled_basals.append(scheduled_basals[i])

    assert len(filtered_types) == len(filtered_starts) == len(filtered_ends)\
        == len(filtered_values) == len(filtered_scheduled_basals),\
        "expected output shapes to match"

    return (
        filtered_types,
        filtered_starts,
        filtered_ends,
        filtered_values,
        filtered_scheduled_basals
        )


def target_glucose_value(
        percent_effect_duration,
        min_value,
        max_value
        ):
    """ Computes a target glucose value for a correction, at a given time
        during the insulin effect duration

    Arguments:
    percent_effect_duration -- percent of time elapsed of the insulin
                               effect duration
    min_value -- minimum (starting) target value
    max_value -- maximum (starting) target value

    Output:
    A target value somewhere between the minimum and maximum (inclusive)
    """
    # The inflection point in time: before it we use minValue,
    # after it we linearly blend from minValue to maxValue
    use_min_value_until_percent = 0.5

    if percent_effect_duration <= use_min_value_until_percent:
        return min_value

    if percent_effect_duration >= 1:
        return max_value

    slope = (
        (max_value - min_value) /
        (1 - use_min_value_until_percent)
        )

    return min_value + slope * (percent_effect_duration
                                - use_min_value_until_percent
                                )


def insulin_correction_units(
        from_value,
        to_value,
        effected_sensitivity
        ):
    """ Computes a total insulin amount necessary to correct a glucose
        differential at a given sensitivity

    Arguments:
    from_value -- starting glucose value
    to_value -- desired glucose value
    effected_sensitivity -- sensitivity (mg/dL/U)

    Output:
    The insulin correction in units
    """
    if effected_sensitivity <= 0:
        return None

    glucose_correction = from_value - to_value
    return glucose_correction / effected_sensitivity


def matches_rate(rate_1, rate_2):
    """ Determine if two rates are the same """
    return abs(rate_1 - rate_2) < sys.float_info.epsilon


def if_necessary(
        temp_basal,
        at_date,
        scheduled_basal_rate,
        last_temp_basal,
        continuation_interval
        ):
    """ Determine whether the recommendation is necessary given the
        current state of the pump

    Arguments:
    temp_basal -- recommended temp basal
    at_date -- date to calculate temp basal at (datetime)
    scheduled_basal_rate -- basal rate scheduled during "at_date"
    last_temp_basal -- the previously set temp basal
    continuation_interval -- duration of time before an ongoing temp basal
                             should be continued with a new command

    Output:
    None (if the scheduled temp basal or basal rate should be allowed to
    continue to run), "cancel" (if the temp basal should be cancelled),
    or the recommended temp basal (if it should be set)
    """
    # Adjust behavior for the currently active temp basal
    if (last_temp_basal
            and last_temp_basal[0].lower() == "tempbasal"
            and last_temp_basal[2] > at_date
       ):
        # If the last temp basal has the same rate, and has more than
        # "continuation_interval" of time remaining, don't set a new temp
        if (matches_rate(temp_basal[0], last_temp_basal[3])
                and (
                    (time_interval_since(last_temp_basal[2], at_date) / 60)
                    > continuation_interval)
           ):
            return None

        # If our new temp matches the scheduled rate, cancel the current temp
        elif matches_rate(temp_basal[0], scheduled_basal_rate):
            return "cancel"

    # If we recommend the in-progress scheduled basal rate, do nothing
    elif matches_rate(temp_basal[0], scheduled_basal_rate):
        return None

    return temp_basal


def insulin_correction(
        prediction_dates, prediction_values,
        target_starts, target_ends, target_mins, target_maxes,
        at_date,
        suspend_threshold_value,
        sensitivity_value,
        model
        ):
    """ Computes a total insulin amount necessary to correct a glucose
        differential at a given sensitivity

    prediction_dates -- dates glucose values were predicted (datetime)
    prediction_values -- predicted glucose values (mg/dL)

    target_starts -- start times for given target ranges (datetime)
    target_ends -- stop times for given target ranges (datetime)
    target_mins -- the lower bounds of target ranges (mg/dL)
    target_maxes -- the upper bounds of target ranges (mg/dL)

    at_date -- date to calculate correction
    suspend_threshold -- value to suspend all insulin delivery at (mg/dL)
    sensitivity_value -- the sensitivity (mg/dL/U)
    model -- list of insulin model parameters in format [DIA, peak_time] if
             exponential model, or [DIA] if Walsh model

    Output:
    A list of insulin correction information. All lists have the type as the
    first index, and may include additional information based on the type.

        Types:
        -1 -- entirely_below_range
            Structure: [type, glucose value to be corrected, minimum target,
                        units of correction insulin]
        0 -- suspend
            Structure: [type]
        1 -- in_range
            Structure: [type]
        2 -- above_range
            Structure: [type, minimum predicted glucose value,
                        glucose value to be corrected, minimum target,
                        units of correction insulin]
    """
    assert len(prediction_dates) == len(prediction_values),\
        "expected input shapes to match"

    assert len(target_starts) == len(target_ends) == len(target_mins)\
        == len(target_maxes), "expected input shapes to match"

    (min_glucose,
     eventual_glucose,
     correcting_glucose,
     min_correction_units
     ) = (None, None, None, None)

    if len(model) == 1:  # if Walsh model
        date_range = [at_date,
                      at_date + timedelta(hours=model[0])
                      ]
    else:
        date_range = [at_date,
                      at_date + timedelta(minutes=model[0])
                      ]

    # For each prediction above target, determine the amount of insulin
    # necessary to correct glucose based on the modeled effectiveness of
    # the insulin at that time
    for i in range(0, len(prediction_dates)):
        if not is_time_between(
                date_range[0],
                date_range[1],
                prediction_dates[i]
            ):
            continue

        # If any predicted value is below the suspend threshold,
        # return immediately
        if prediction_values[i] < suspend_threshold_value:
            return [0, prediction_dates[i], prediction_values[i]]

        # Update range statistics
        if not min_glucose or prediction_values[i] < min_glucose[1]:
            min_glucose = [prediction_dates[i], prediction_values[i]]

        eventual_glucose = [prediction_dates[i], prediction_values[i]]
        predicted_glucose_value = prediction_values[i]
        time = time_interval_since(
            prediction_dates[i],
            at_date
            ) / 60

        # Compute the target value as a function of time since the dose started
        target_value = target_glucose_value(
            (time /
             (
                 (60 * model[0]) if len(model) == 1
                 else model[0]
             )
            ),
            suspend_threshold_value,
            (find_ratio_at_time(
                target_starts,
                target_ends,
                target_maxes,
                at_date
                ) -
             find_ratio_at_time(
                 target_starts,
                 target_ends,
                 target_mins,
                 at_date
                 )
             ) / 2
        )

        # Compute the dose required to bring this prediction to target:
        # dose = (Glucose delta) / (% effect × sensitivity)
        if len(model) == 1:  # if Walsh model
            percent_effected = 1 - walsh_percent_effect_remaining(
                time,
                model[0]
            )
        else:
            percent_effected = 1 - percent_effect_remaining(
                time,
                model[0],
                model[1]
            )

        effected_sensitivity = percent_effected * sensitivity_value

        correction_units = insulin_correction_units(
            predicted_glucose_value,
            target_value,
            effected_sensitivity
        )

        if not correction_units or correction_units <= 0:
            continue

        # Update the correction only if we've found a new minimum
        if min_correction_units:
            if correction_units >= min_correction_units:
                continue

        correcting_glucose = [prediction_dates[i], prediction_values[i]]
        min_correction_units = correction_units

    if not eventual_glucose or not min_glucose:
        return None

    # Choose either the minimum glucose or eventual glucose as correction delta
    min_glucose_targets = [
        find_ratio_at_time(
            target_starts,
            target_ends,
            target_mins,
            min_glucose[0]
        ),
        find_ratio_at_time(
            target_starts,
            target_ends,
            target_maxes,
            min_glucose[0]
        )
    ]
    eventual_glucose_targets = [
        find_ratio_at_time(
            target_starts,
            target_ends,
            target_mins,
            eventual_glucose[0]
            ),
        find_ratio_at_time(
            target_starts,
            target_ends,
            target_maxes,
            eventual_glucose[0]
        )
    ]

    # Treat the mininum glucose when both are below range
    if (min_glucose[1] < min_glucose_targets[0]
            and eventual_glucose[1] < min_glucose_targets[0]
       ):
        time = time_interval_since(min_glucose[0], at_date) / 60
        # For time = 0, assume a small amount effected.
        # This will result in large (negative) unit recommendation
        # rather than no recommendation at all.
        if len(model) == 1:
            percent_effected = max(
                sys.float_info.epsilon,
                1 - walsh_percent_effect_remaining(at_date, model[0])
                )
        else:
            percent_effected = max(
                sys.float_info.epsilon,
                1 - percent_effect_remaining(at_date, model[0], model[1])
                )

        units = insulin_correction_units(
            min_glucose[1],
            sum(min_glucose_targets) / len(min_glucose_targets),
            sensitivity_value * percent_effected
            )
        if not units:
            return None

        return [
            -1,
            min_glucose[1],
            min_glucose_targets[0],
            units
            ]

    elif (eventual_glucose[1] > eventual_glucose_targets[1]
          and min_correction_units
          and correcting_glucose
         ):
        return [
            2,
            min_glucose[1],
            correcting_glucose[1],
            eventual_glucose_targets[0],
            min_correction_units
            ]
    else:
        return [1]


def as_temp_basal(
        correction,
        scheduled_basal_rate,
        max_basal_rate,
        duration,
        rate_rounder=None
        ):
    """ Determines temp basal over duration needed to perform the correction

    Arguments:
    correction -- list of information about the total amount of insulin
                  needed to correct BGs
    scheduled_basal_rate -- scheduled basal rate at time correction is given
    max_basal_rate -- the maximum allowed basal rate
    duration -- duration of the temporary basal
    rate_rounder -- the smallest fraction of a unit supported in basal delivery

    Output:
    Temp basal recommendation in form [temp basal rate, temp basal duration]
    """
    rate = (
        correction[len(correction) - 1] / (duration / 60)
        if correction[0] in [-1, 2] else 0
    )
    # if it's not a suspend, add in the scheduled basal rate
    if correction[0] in [-1, 1, 2]:
        rate += scheduled_basal_rate

    rate = min(max_basal_rate, max(0, rate))

    # round to the appropriate increment for the insulin pump
    if rate_rounder:
        rate_rounder = 1 / rate_rounder
        rate = round(rate * rate_rounder) / rate_rounder

    return [rate, duration]


def recommended_temp_basal(
        glucose_dates, glucose_values,
        target_starts, target_ends, target_mins, target_maxes,
        at_date,
        suspend_threshold,
        sensitivity_starts, sensitivity_ends, sensitivity_values,
        model,
        basal_starts, basal_rates, basal_minutes,
        max_basal_rate,
        last_temp_basal,
        duration=30,
        continuation_interval=11,
        rate_rounder=None
        ):
    """ Recommends a temporary basal rate to conform a glucose prediction
    timeline to a correction range

    Returns None if normal scheduled basal or active temporary basal is
    sufficient

    Arguments:
    glucose_dates -- dates of glucose values (datetime)
    glucose_values -- glucose values (in mg/dL)

    target_starts -- start times for given target ranges (datetime)
    target_ends -- stop times for given target ranges (datetime)
    target_mins -- the lower bounds of target ranges (mg/dL)
    target_maxes -- the upper bounds of target ranges (mg/dL)

    at_date -- date to calculate the temp basal at
    suspend_threshold -- value to suspend all insulin delivery at (mg/dL)

    sensitivity_starts -- list of time objects of start times of
                          given insulin sensitivity values
    sensitivity_ends -- list of time objects of start times of
                        given insulin sensitivity values
    sensitivity_values -- list of sensitivities (mg/dL/U)

    model -- list of insulin model parameters in format [DIA, peak_time] if
             exponential model, or [DIA] if Walsh model

    basal_starts -- list of times the basal rates start at
    basal_rates -- list of basal rates(U/hr)
    basal_minutes -- list of basal lengths (in mins)

    max_basal_rate -- max basal rate that Loop can give (U/hr)
    last_temp_basal -- list of last temporary basal information in format
                       [type, start time, end time, basal rate]
    duration -- length of the temp basal (mins)
    continuation_interval -- length of time before an ongoing temp basal
                             should be continued with a new command (mins)
    rate_rounder -- the smallest fraction of a unit supported in basal
                    delivery; if None, no rounding is performed

    Output:
    The recommended temporary basal rate and duration
    """
    # last temp basal: [type, start_date, end_date, value]
    assert len(glucose_dates) == len(glucose_values),\
        "expected input shapes to match"

    assert len(target_starts) == len(target_ends) == len(target_mins)\
        == len(target_maxes), "expected input shapes to match"

    assert len(sensitivity_starts) == len(sensitivity_ends)\
        == len(sensitivity_values), "expected input shapes to match"

    assert len(basal_starts) == len(basal_rates) == len(basal_minutes),\
        "expected input shapes to match"

    sensitivity_value = find_ratio_at_time(
        sensitivity_starts, sensitivity_ends, sensitivity_values,
        at_date
        )

    correction = insulin_correction(
        glucose_dates, glucose_values,
        target_starts, target_ends, target_mins, target_maxes,
        at_date,
        suspend_threshold,
        sensitivity_value,
        model
        )

    scheduled_basal_rate = find_ratio_at_time(
        basal_starts, [], basal_rates,
        at_date
        )

    if correction[0] == 2 and correction[1] < correction[3]:
        max_basal_rate = scheduled_basal_rate

    temp_basal = as_temp_basal(
        correction,
        scheduled_basal_rate,
        max_basal_rate,
        duration,
        rate_rounder
        )

    return if_necessary(
        temp_basal,
        at_date,
        scheduled_basal_rate,
        last_temp_basal,
        continuation_interval
        )