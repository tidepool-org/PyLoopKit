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
from enum import Enum
import sys

from pyloopkit.insulin_math import is_time_between, find_ratio_at_time
from pyloopkit.date import time_interval_since
from pyloopkit.dose import DoseType
from pyloopkit.walsh_insulin_model import walsh_percent_effect_remaining
from pyloopkit.exponential_insulin_model import percent_effect_remaining


class Correction(Enum):
    suspend = 0
    in_range = 1
    above_range = 2
    entirely_below_range = 3
    cancel = 4


def filter_date_range_for_doses(
        types, starts, ends, values, delivered_units,
        start_date,
        end_date
        ):
    """ Returns an array of elements filtered by the specified date range.

    Arguments:
    types -- String of type of dose (basal, bolus, etc)
    starts -- start dates (datetime)
    ends -- end dates (datetime)
    values -- glucose values

    start_date -- the earliest date of elements to return
    end_date -- the last date of elements to return

    Output:
    Filtered dates in format (types, starts, ends, values)
    """
    # ends might not necesarily be the same length as starts/values
    # because not all types have "end dates"
    assert len(types) == len(starts) == len(values) == len(delivered_units),\
        "expected input shapes to match"

    (filtered_types,
     filtered_starts,
     filtered_ends,
     filtered_values,
     filtered_delivered_units
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
        filtered_delivered_units.append(delivered_units[i])

    assert len(filtered_types) == len(filtered_starts) == len(filtered_ends)\
        == len(filtered_values) == len(filtered_delivered_units),\
        "expected output shapes to match"

    return (
        filtered_types,
        filtered_starts,
        filtered_ends,
        filtered_values,
        filtered_delivered_units
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
    continue to run), cancel (if the temp basal should be cancelled),
    or the recommended temp basal (if it should be set)
    """
    # Adjust behavior for the currently active temp basal
    if (last_temp_basal
            and last_temp_basal[0] in [DoseType.tempbasal, DoseType.basal]
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
            return Correction.cancel

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
        - entirely_below_range
            Structure: [type, glucose value to be corrected, minimum target,
                        units of correction insulin]
        - suspend
            Structure: [type, min glucose value]
        - in_range
            Structure: [type]
        - above_range
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
     ) = ([], None, None, None)

    # only calculate a correction if the prediction is between
    # "now" and now + DIA
    if len(model) == 1:  # if Walsh model
        date_range = [at_date,
                      at_date + timedelta(hours=model[0])
                      ]
    else:
        date_range = [at_date,
                      at_date + timedelta(minutes=model[0])
                      ]

    # if we don't know the suspend threshold, it defaults to the lower
    # bound of the correction range at the time the "loop" is being run at
    if not suspend_threshold_value:
        suspend_threshold_value = find_ratio_at_time(
            target_starts,
            target_ends,
            target_mins,
            at_date
            )

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
            return [Correction.suspend, prediction_values[i]]

        # Update range statistics
        if not min_glucose or prediction_values[i] < min_glucose[1]:
            min_glucose = [prediction_dates[i], prediction_values[i]]

        eventual_glucose = [prediction_dates[i], prediction_values[i]]
        predicted_glucose_value = prediction_values[i]
        time = time_interval_since(
            prediction_dates[i],
            at_date
            ) / 60

        average_target = (
            find_ratio_at_time(
                target_starts,
                target_ends,
                target_maxes,
                prediction_dates[i]
                ) +
            find_ratio_at_time(
                target_starts,
                target_ends,
                target_mins,
                prediction_dates[i]
                )
            ) / 2
        # Compute the target value as a function of time since the dose started
        target_value = target_glucose_value(
            (time /
             (
                 (60 * model[0]) if len(model) == 1
                 else model[0]
             )
            ),
            suspend_threshold_value,
            average_target
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

        # calculate the Units needed to correct that predicted glucose value
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
                1 - walsh_percent_effect_remaining(time, model[0])
                )
        else:
            percent_effected = max(
                sys.float_info.epsilon,
                1 - percent_effect_remaining(time, model[0], model[1])
                )

        units = insulin_correction_units(
            min_glucose[1],
            sum(min_glucose_targets) / len(min_glucose_targets),
            sensitivity_value * percent_effected
            )

        if not units:
            return None

        # we're way below target
        return [
            Correction.entirely_below_range,
            min_glucose[1],
            min_glucose_targets[0],
            units
            ]

    # we're above target
    elif (eventual_glucose[1] > eventual_glucose_targets[1]
          and min_correction_units
          and correcting_glucose
         ):
        return [
            Correction.above_range,
            min_glucose[1],
            correcting_glucose[1],
            eventual_glucose_targets[0],
            min_correction_units
            ]
    # we're in range
    else:
        return [Correction.in_range]


def as_temp_basal(
        correction,
        scheduled_basal_rate,
        max_basal_rate,
        duration,
        rate_rounder=None
        ):
    """ Determine temp basal over duration needed to perform the correction

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
        if correction[0] in [
            Correction.entirely_below_range, Correction.above_range
        ] else 0
    )
    # if it's not a suspend, add in the scheduled basal rate
    if not correction[0] == Correction.suspend:
        rate += scheduled_basal_rate

    rate = min(max_basal_rate, max(0, rate))

    # round to the appropriate increment for the insulin pump
    if rate_rounder:
        rate_rounder = 1 / rate_rounder
        rate = round(rate * rate_rounder) / rate_rounder

    return [rate, duration]


def bolus_recommendation_notice(correction):
    """ Make a bolus recommendation based on an insulin correction """
    if correction[0] == Correction.suspend:
        return ["glucoseBelowSuspendThreshold", correction[1]]

    if correction[0] in [Correction.entirely_below_range, Correction.in_range]:
        return None

    if correction[0] == Correction.above_range:
        # if we're recommending units but the minimum glucose is below target
        if correction[4] > 0 and correction[1] < correction[3]:
            return ["predictedGlucoseBelowTarget", correction[1]]

    return None


def as_bolus(
        correction,
        pending_insulin,
        max_bolus,
        volume_rounder
        ):
    """  Determine the bolus needed to perform the correction

    Arguments:
    correction -- list of information about the total amount of insulin
                  needed to correct BGs
    pending_insulin -- number of units expected to be delivered, but not yet
                       reflected in the correction
    max_bolus -- the maximum allowed bolus
    volume_rounder -- the smallest fraction of a unit supported in
                      insulin delivery

    Output:
    A bolus recommendation in form [units of bolus, pending insulin,
                                    recommendation]
    """
    correction_units = (
        correction[len(correction) - 1]
        if correction[0] in [
            Correction.above_range, Correction.entirely_below_range
        ] else 0
    )
    units = correction_units - pending_insulin
    units = min(max_bolus, max(0, units))

    if volume_rounder:
        volume_rounder = 1 / volume_rounder
        units = round(units * volume_rounder) / volume_rounder

    recommendation = bolus_recommendation_notice(correction)

    return [units, pending_insulin, recommendation]


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
    The recommended temporary basal in the format [rate, duration]
    """
    assert len(glucose_dates) == len(glucose_values),\
        "expected input shapes to match"

    assert len(target_starts) == len(target_ends) == len(target_mins)\
        == len(target_maxes), "expected input shapes to match"

    assert len(sensitivity_starts) == len(sensitivity_ends)\
        == len(sensitivity_values), "expected input shapes to match"

    assert len(basal_starts) == len(basal_rates) == len(basal_minutes),\
        "expected input shapes to match"

    if (not glucose_dates
            or not target_starts
            or not sensitivity_starts
            or not basal_starts
       ):
        return None

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

    if (correction[0] == Correction.above_range
            and correction[1] < correction[3]):
        max_basal_rate = scheduled_basal_rate

    temp_basal = as_temp_basal(
        correction,
        scheduled_basal_rate,
        max_basal_rate,
        duration,
        rate_rounder
        )

    recommendation = if_necessary(
        temp_basal,
        at_date,
        scheduled_basal_rate,
        last_temp_basal,
        continuation_interval
        )

    # convert a "cancel" into zero-temp, zero-duration basal
    if recommendation == Correction.cancel:
        return [0, 0]

    return recommendation


def recommended_bolus(
        glucose_dates, glucose_values,
        target_starts, target_ends, target_mins, target_maxes,
        at_date,
        suspend_threshold,
        sensitivity_starts, sensitivity_ends, sensitivity_values,
        model,
        pending_insulin,
        max_bolus,
        volume_rounder=None
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

    pending_insulin -- number of units expected to be delivered, but not yet
                       reflected in the correction
    max_bolus -- the maximum allowable bolus value in Units
    volume_rounder -- the smallest fraction of a unit supported in insulin
                      delivery; if None, no rounding is performed

    Output:
    A bolus recommendation
    """
    assert len(glucose_dates) == len(glucose_values),\
        "expected input shapes to match"

    assert len(target_starts) == len(target_ends) == len(target_mins)\
        == len(target_maxes), "expected input shapes to match"

    assert len(sensitivity_starts) == len(sensitivity_ends)\
        == len(sensitivity_values), "expected input shapes to match"

    if (not glucose_dates
            or not target_starts
            or not sensitivity_starts
       ):
        return [0, 0, None]

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

    bolus = as_bolus(
        correction,
        pending_insulin,
        max_bolus,
        volume_rounder
        )

    if bolus[0] < 0:
        bolus = 0

    return bolus
