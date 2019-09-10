#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 09:53:33 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/GlucoseKit/GlucoseMath.swift
"""
# pylint: disable=C0103, R0913, R0914
# disable pylint errors for too many arguments/variables
import math
from datetime import timedelta

from pyloopkit.date import time_interval_since
from pyloopkit.loop_math import simulation_date_range_for_samples


def linear_regression(x_list, y_list):
    """ Calculates slope and intercept using linear regression
    This implementation is not suited for large datasets

    Arguments:
    tuples_list -- An array of tuples containing x and y values

    Output:
    A tuple of slope and intercept values
    """
    assert len(x_list) == len(y_list), "expected input shapes to match"
    sum_x = 0.0
    sum_y = 0.0
    sum_xy = 0.0
    sum_x_squared = 0.0
    sum_y_squared = 0.0
    count = len(x_list)

    for i in range(0, len(x_list)):  # pylint: disable=C0200
        x = x_list[i]
        y = y_list[i]
        sum_x += x
        sum_y += y
        sum_xy += x * y
        sum_x_squared += x * x
        sum_y_squared += y * y

    try:
        slope = (((count * sum_xy) - (sum_x * sum_y)) /
                 ((count * sum_x_squared) - (sum_x * sum_x)))

        # I didn't include the intercept because it was unused
    except ZeroDivisionError:
        return float('NaN')

    return slope


def is_calibrated(display_list):
    """ Checks if no calibration entries are present
    Runtime: O(n)

    Arguments:
    obj_list -- list of Glucose-related objects with is_display_only
                property

    Output:
    Whether the collection contains calibration entries
    """
    return True in display_list


def is_continuous(date_list, delta=5):
    """ Checks whether the collection can be considered continuous

    Arguments:
    date_list -- list of datetime objects
    delta -- the (expected) time interval between CGM values

    Output:
    Whether the collection is continuous
    """
    try:
        return (
            abs(time_interval_since(date_list[0], date_list[-1]))
            < delta * (len(date_list)) * 60
        )

    except IndexError:
        print("Out of bounds error: list doesn't contain date values")
        return False


def has_single_provenance(provenance_list):
    """ Checks whether the collection is all from the same source
    Runtime: O(n)

    Arguments:
    provenance_list -- list of Glucose-related objects with
                provenance_identifier property

    Output:
    True if the samples are from same source
    """
    try:
        first_provenance = provenance_list[0]

    except IndexError:
        print("Out of bounds error: list doesn't contain objects")

    for provenance in provenance_list:
        if provenance != first_provenance:
            return False

    return True


def linear_momentum_effect(
        date_list, glucose_value_list, display_list, provenance_list,
        duration=30,
        delta=5
    ):
    """ Calculates the short-term predicted momentum effect using
        linear regression

    Arguments:
    date_list -- list of datetime objects
    glucose_value_list -- list of glucose values (unit: mg/dL)
    display_list -- list of display_only booleans
    provenance_list -- list of provenances (Strings)
    duration -- the duration of the effects
    delta -- the time differential for the returned values

    Output:
    tuple with format (date_of_glucose_effect, value_of_glucose_effect)
    """
    assert len(date_list) == len(glucose_value_list) == len(display_list)\
        == len(provenance_list), "expected input shape to match"

    if (len(date_list) <= 2 or not is_continuous(date_list)
            or is_calibrated(display_list)
            or not has_single_provenance(provenance_list)
       ):
        return ([], [])

    first_time = date_list[0]
    last_time = date_list[-1]
    (start_date, end_date) = simulation_date_range_for_samples(
        [last_time], [], duration, delta
    )

    def create_times(time):
        return abs(time_interval_since(time, first_time))

    slope = linear_regression(
        list(map(create_times, date_list)), glucose_value_list
    )

    if math.isnan(slope) or math.isinf(slope):
        return ([], [])

    date = start_date
    momentum_effect_dates = []
    momentum_effect_values = []

    while date <= end_date:
        value = (max(0, time_interval_since(date, last_time)) * slope)
        momentum_effect_dates.append(date)
        momentum_effect_values.append(value)
        date += timedelta(minutes=delta)

    assert len(momentum_effect_dates) == len(momentum_effect_values),\
        "expected output shape to match"
    return (momentum_effect_dates, momentum_effect_values)


def counteraction_effects(
        dates, glucose_values, displays, provenances,
        effect_dates, effect_values
    ):
    """ Calculates a timeline of effect velocity (glucose/time) observed
        in glucose readings that counteract the specified effects.

    Arguments:
    dates -- list of datetime objects of dates of glucose values
    glucose_values -- list of glucose values (unit: mg/dL)
    displays -- list of display_only booleans
    provenances -- list of provenances (Strings)

    effect_dates -- list of datetime objects associated with a glucose effect
    effect_values -- list of values associated with a glucose effect

    Output:
    An array of velocities describing the change in glucose samples
    compared to the specified effects
    """
    assert len(dates) == len(glucose_values) == len(displays)\
        == len(provenances), "expected input shape to match"
    assert len(effect_dates) == len(effect_values),\
        "expected input shape to match"

    if not dates or not effect_dates:
        return ([], [], [])

    effect_index = 0
    start_glucose = glucose_values[0]
    start_date = dates[0]
    start_prov = provenances[0]
    start_display = displays[0]

    start_dates = []
    end_dates = []
    velocities = []

    for i in range(1, len(dates)):
        # Find a valid change in glucose, requiring identical
        # provenance and no calibration
        glucose_change = glucose_values[i] - start_glucose
        time_interval = time_interval_since(dates[i], start_date)

        if time_interval <= 4 * 60:
            continue

        if (not start_prov == provenances[i]
                or start_display
                or displays[i]
           ):
            start_glucose = glucose_values[i]
            start_date = dates[i]
            start_prov = provenances[i]
            start_display = displays[i]
            continue

        start_effect_date = None
        start_effect_value = None
        end_effect_date = None
        end_effect_value = None

        for j in range(effect_index, len(effect_dates)):
            # if one of the start_effect properties doesn't exist and
            # the glucose effect at position "j" will happen after the
            # starting glucose date, then make start_effect equal to that
            # effect
            if (not start_effect_date
                    and effect_dates[j] >= start_date
               ):
                start_effect_date = effect_dates[j]
                start_effect_value = effect_values[j]

            elif (not end_effect_date
                  and effect_dates[j] >= dates[i]
                 ):
                end_effect_date = effect_dates[j]
                end_effect_value = effect_values[j]
                break

            effect_index += 1

        if end_effect_value is None:
            continue
        effect_change = end_effect_value - start_effect_value

        discrepancy = glucose_change - effect_change

        average_velocity = discrepancy / time_interval * 60

        start_dates.append(start_date)
        end_dates.append(dates[i])
        velocities.append(average_velocity)

        start_glucose = glucose_values[i]
        start_date = dates[i]
        start_prov = provenances[i]
        start_display = displays[i]

    assert len(start_dates) == len(end_dates) == len(velocities),\
        "expected output shape to match"
    return (start_dates, end_dates, velocities)
