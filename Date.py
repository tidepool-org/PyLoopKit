#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 08:45:26 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/Extensions/Date.swift
"""
from loop_kit_tests import date_formatter
import math
import datetime


# input - datetime object
# output - returns the number of seconds
#          since January, 1st, 2001: 12:00 am (mid night)
def time_interval_since_reference_date(actual_time):
    ref_time = date_formatter("2001-01-01T00:00:00")
    dif = abs(actual_time - ref_time).total_seconds()
    return dif


# input - two datetime objects
# output - the seconds between two times (with a sign)
def time_interval_since(date_1, date_2):
    return (date_1 - date_2).total_seconds()


def date_floored_to_time_interval(time, interval):
    if interval == 0:
        return time
    ref_time = date_formatter("2001-01-01T00:00:00")
    # this assumes the interval is in mins
    floored_delta = (math.floor(time_interval_since_reference_date(time)
                     / interval / 60) * interval * 60)

    return ref_time + datetime.timedelta(seconds=floored_delta)


def date_ceiled_to_time_interval(time, interval):
    if interval == 0:
        return time
    ref_time = date_formatter("2001-01-01T00:00:00")
    # this assumes the interval is in mins
    ceiled_delta = (math.ceil(time_interval_since_reference_date(time)
                    / interval / 60) * interval * 60)

    return ref_time + datetime.timedelta(seconds=ceiled_delta)
