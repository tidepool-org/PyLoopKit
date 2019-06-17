#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 08:45:26 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/Extensions/Date.swift
"""
import math
import datetime


def time_interval_since_reference_date(actual_time):
    """ Calculates seconds since since January, 1st, 2001 @ 12:00 AM

    Keyword arguments:
    actual_time -- datetime object to compare to Jan 1st, 2001 @ 12:00 AM

    Output:
    Num of seconds since Jan 1st, 2001 @ 12:00 AM (without a sign)
    """
    ref_time = datetime.datetime.fromisoformat("2001-01-01T00:00:00")
    dif = abs(actual_time - ref_time).total_seconds()
    return dif


def time_interval_since(date_1, date_2):
    """ Calculates seconds between two times

    Keyword arguments:
    date_1 -- datetime object #1
    date_2 -- datetime object #2

    Output:
    Num of seconds between the two times (with a sign)
    """
    return (date_1 - date_2).total_seconds()


def date_floored_to_time_interval(time_, interval):
    """ Floors a datetime object to a particular minute interval

    Keyword arguments:
    time -- datetime object to be floored
    interval -- interval to floor the time to, measured in minutes

    Output:
    Floored datetime object

    Example:
        2/2/19 2:03 PM, interval=5 -> 2/2/19 2:00 PM
    """
    if interval == 0:
        return time_
    ref_time = datetime.datetime.fromisoformat("2001-01-01T00:00:00")
    # this assumes the interval is in mins
    floored_delta = (math.floor(time_interval_since_reference_date(time_) /
                                interval / 60) * interval * 60)

    return ref_time + datetime.timedelta(seconds=floored_delta)


def date_ceiled_to_time_interval(time, interval):
    """ Ceils a datetime object to a particular minute interval
=
    Keyword arguments:
    time -- datetime object to be ceiled
    interval -- interval to ceil the time to, measured in minutes

    Output:
    Ceiled datetime object

    Example:
        2/2/19 2:03 PM, interval=5 -> 2/2/19 2:05 PM
    """
    if interval == 0:
        return time
    ref_time = datetime.datetime.fromisoformat("2001-01-01T00:00:00")
    # this assumes the interval is in mins
    ceiled_delta = (math.ceil(time_interval_since_reference_date(time) /
                              interval / 60) * interval * 60)

    return ref_time + datetime.timedelta(seconds=ceiled_delta)
