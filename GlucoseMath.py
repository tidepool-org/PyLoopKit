#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 09:53:33 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/GlucoseKit/GlucoseMath.swift
"""
from Date import time_interval_since
from LoopMath import simulation_date_range_for_samples
from GlucoseEffect import GlucoseEffect
from LoopKitTests import HKQuantity
import math
from datetime import timedelta


#    Calculates slope and intercept using linear regression
#    This implementation is not suited for large datasets.
#    - parameter points: An array of tuples containing x and y values
#    - returns: A tuple of slope and intercept values
def linear_regression(tuples_list):
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
    intercept = ((sum_y * sum_x_squared - (sum_x * sum_xy)) /
                 (count * sum_x_squared - (sum_x * sum_x)))

    return (slope, intercept)


# Whether the collection contains no calibration entries
# Runtime: O(n)
def is_calibrated(obj_list):

    def filter_func(obj):
        return obj.is_display_only

    return len(list(filter(filter_func, obj_list))) == 0


# Whether the collection can be considered continuous
# - Parameters:
#   - obj_list: list of Glucose-related objects with start_date property
# - Returns: True if the samples are continuous
def is_continuous(obj_list, interval=5):
    try:
        first = obj_list[0]
        last = obj_list[len(obj_list)-1]
        return (abs(time_interval_since(first.start_date, last.start_date))/60
                < interval * (len(obj_list) - 1))

    except IndexError:
        print("Out of bounds error: list doesn't contain objects")
        return False

    except Exception as e:
        print("Unexpected error: " + str(e))


# Whether the collection is all from the same source.
# Runtime: O(n)
# - Parameters:
#   - obj_list: list of Glucose-related objects with provenance_identifier
#     property
# - Returns: True if the samples are from same source
def has_single_provenance(obj_list):
    try:
        first_provenance = obj_list[0].provenance_identifier

    except IndexError:
        print("Out of bounds error: list doesn't contain objects")

    for sample in obj_list:
        if sample.provenance_identifier != first_provenance:
            return False

    return True


# Calculates the short-term predicted momentum effect using linear regression
# - Parameters:
#   - object_list: List of Glucose-related objects
#   - duration: The duration of the effects
#   - delta: The time differential for the returned values
# - Returns: An array of glucose effects
def linear_momentum_effect(object_list, duration=30, delta=5):
    if (len(object_list) <= 2 or not is_continuous(object_list)
            or not is_calibrated(object_list)
            or not has_single_provenance(object_list)):
        return []

    first_sample = object_list[0]
    last_sample = object_list[len(object_list)-1]
    (start_date, end_date) = simulation_date_range_for_samples([last_sample],
                                                               duration, delta)

    def create_tuples(object_):
        return (time_interval_since(object_.start_date,
                                    first_sample.start_date),
                object_.quantity.double_value)

    (slope, intercept) = linear_regression(list(map(create_tuples,

    if math.isNaN(slope) or math.isinf(slope):
        return []

    date = start_date
    values = []

    while date <= end_date:
        value = max(0, time_interval_since(date,
                                           last_sample.start_date)) * slope
        values.append(GlucoseEffect(date, HKQuantity("mg/dL", value)))
        date += timedelta(minutes=delta)

    return values
