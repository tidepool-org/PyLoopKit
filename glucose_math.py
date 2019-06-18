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
from glucose_effect import GlucoseEffect


def linear_regression(tuples_list):
    """ Calculates slope and intercept using linear regression
    This implementation is not suited for large datasets

    Keyword arguments:
    tuples_list -- An array of tuples containing x and y values

    Output:
    A tuple of slope and intercept values
    """
    sum_x = 0.0
    sum_y = 0.0
    sum_xy = 0.0
    sum_x_squared = 0.0
    sum_y_squared = 0.0
    count = len(tuples_list)

    for tuple_ in tuples_list:
        x = tuple_[0]
        y = tuple_[1]
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
    Whether the collection contains no calibration entries
    """
    def filter_func(obj):
        return obj.is_display_only

    return len(list(filter(filter_func, obj_list))) == 0


def is_continuous(obj_list, interval=5):
    """ Checks whether the collection can be considered continuous

    Keyword arguments:
    obj_list -- list of Glucose-related objects with start_date property

    Output:
    Whether the collection is continuous
    """
    try:
        first = obj_list[0]
        last = obj_list[len(obj_list)-1]
        return (abs(time_interval_since(first.start_date, last.start_date))/60
                <= interval * (len(obj_list) - 1))

    except IndexError:
        print("Out of bounds error: list doesn't contain objects")
        return False


def has_single_provenance(obj_list):
    """ Checks whether the collection is all from the same source
    Runtime: O(n)

    Keyword arguments:
    obj_list -- list of Glucose-related objects with
                provenance_identifier property

    Output:
    True if the samples are from same source
    """
    try:
        first_provenance = obj_list[0].provenance_identifier

    except IndexError:
        print("Out of bounds error: list doesn't contain objects")

    for sample in obj_list:
        if sample.provenance_identifier != first_provenance:
            return False

    return True


def linear_momentum_effect(object_list, duration=30, delta=5):
    """ Calculates the short-term predicted momentum effect using
        linear regression

    Keyword arguments:
    obj_list -- list of Glucose-related objects
    duration -- the duration of the effects
    delta -- the time differential for the returned values

    Output:
    an array of glucose effects
    """
    if (len(object_list) <= 2 or not is_continuous(object_list)
            or not is_calibrated(object_list)
            or not has_single_provenance(object_list)):
        return []

    first_sample = object_list[0]
    last_sample = object_list[len(object_list)-1]
    (start_date, end_date) = simulation_date_range_for_samples([last_sample],
                                                               duration, delta)

    def create_tuples(object_):
        return (abs(time_interval_since(object_.start_date,
                                        first_sample.start_date)),
                object_.quantity)

    slope = linear_regression(list(map(create_tuples, object_list)))[0]

    if math.isnan(slope) or math.isinf(slope):
        return []

    date = start_date
    values = []

    while date <= end_date:
        value = (max(0, time_interval_since(date, last_sample.start_date))
                 * slope)
        values.append(GlucoseEffect(date, value))
        date += timedelta(minutes=delta)

    return values
