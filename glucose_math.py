#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 09:53:33 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/GlucoseKit/GlucoseMath.swift
"""
import math
from datetime import timedelta
from date import time_interval_since
from loop_math import simulation_date_range_for_samples


def linear_regression(x_list, y_list):
    """ Calculates slope and intercept using linear regression
    This implementation is not suited for large datasets

    Keyword arguments:
    tuples_list -- An array of tuples containing x and y values

    Output:
    A tuple of slope and intercept values
    """
    assert len(x_list) == len(y_list), "expected input shape to match"
    sum_x = 0.0
    sum_y = 0.0
    sum_xy = 0.0
    sum_x_squared = 0.0
    sum_y_squared = 0.0
    count = len(x_list)

    for i in range(0, x_list):
        x = x_list[i]
        y = y_list[i]
        sum_x += x
        sum_y += y
        sum_xy += x * y
        sum_x_squared += x * x
        sum_y_squared += y * y

    slope = (((count * sum_xy) - (sum_x * sum_y)) /
             ((count * sum_x_squared) - (sum_x * sum_x)))

    # I didn't include the intercept because it was unused

    return slope


def is_calibrated(display_list):
    """ Checks if no calibration entries are present
    Runtime: O(n)

    Keyword arguments:
    obj_list -- list of Glucose-related objects with is_display_only
                property

    Output:
    Whether the collection contains calibration entries
    """
    return True in display_list


def is_continuous(date_list, interval=5):
    """ Checks whether the collection can be considered continuous

    Keyword arguments:
    date_list -- list of datetime objects

    Output:
    Whether the collection is continuous
    """
    try:
        return (abs(time_interval_since(date_list[0], date_list[-1]))/60
                <= interval * (len(date_list) - 1))

    except IndexError:
        print("Out of bounds error: list doesn't contain date values")
        return False


def has_single_provenance(prov_list):
    """ Checks whether the collection is all from the same source
    Runtime: O(n)

    Keyword arguments:
    obj_list -- list of Glucose-related objects with
                provenance_identifier property

    Output:
    True if the samples are from same source
    """
    try:
        first_provenance = prov_list[0]

    except IndexError:
        print("Out of bounds error: list doesn't contain objects")

    for prov in prov_list:
        if prov != first_provenance:
            return False

    return True


def linear_momentum_effect(date_list, glucose_value_list, display_list,
                           provenance_list, duration=30, delta=5):
    """ Calculates the short-term predicted momentum effect using
        linear regression

    Keyword arguments:
    date_list -- list of datetime objects
    glucose_value_list -- list of glucose values (unit: mg/dL)
    display_list -- list of display_only booleans
    provenance_list -- list of provenances (Strings)
    duration -- the duration of the effects
    delta -- the time differential for the returned values

    Output:
    an array of glucose effects
    """
    assert len(date_list) == len(glucose_value_list) == len(display_list)\
        == len(provenance_list), "expected input shape to match"

    if (len(date_list) <= 2 or not is_continuous(date_list)
            or is_calibrated(display_list)
            or not has_single_provenance(provenance_list)):
        return []

    first_time = date_list[0]
    last_time = date_list[-1]
    (start_date, end_date) = simulation_date_range_for_samples([last_time], [],
                                                               duration, delta)

    def create_times(time):
        return abs(time_interval_since(time, first_time))

    slope = linear_regression(list(map(create_times, date_list)),
                              glucose_value_list)

    if math.isnan(slope) or math.isinf(slope):
        return []

    date = start_date
    glucose_effect_date = []
    glucose_effect_value = []

    while date <= end_date:
        value = (max(0, time_interval_since(date, last_time))
                 * slope)
        glucose_effect_date.append(date)
        glucose_effect_value.append(value)
        date += timedelta(minutes=delta)

    return (glucose_effect_date, glucose_effect_value)
