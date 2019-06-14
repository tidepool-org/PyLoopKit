#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 08:45:26 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/Extensions/Date.swift
"""
from LoopKitTests import date_formatter
import math
import datetime


# time_interval_since_reference_date returns the number of seconds
# since January, 1st, 2001: 12:00 am (mid night)
def time_interval_since_reference_date(obj):
    ref_time = date_formatter("2001-01-01T00:00:00")
    actual_time = obj.start_date
    dif = abs(actual_time - ref_time)
    return dif


def date_floored_to_time_interval(obj, interval):
    if interval == 0:
        return obj
    ref_time = date_formatter("2001-01-01T00:00:00")
    # this assumes the interval is in mins
    floored_delta = (math.floor(time_interval_since_reference_date(obj)
                     / interval / 60) * interval * 60)

    return ref_time + datetime.timedelta(seconds=floored_delta)


def date_ceiled_to_time_interval(obj, interval):
    if interval == 0:
        return obj
    ref_time = date_formatter("2001-01-01T00:00:00")
    # this assumes the interval is in mins
    ceiled_delta = (math.ceil(time_interval_since_reference_date(obj)
                    / interval / 60) * interval * 60)

    return ref_time + datetime.timedelta(seconds=ceiled_delta)
