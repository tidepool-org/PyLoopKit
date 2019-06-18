#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 10:40:48 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
            57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/LoopMath.swift
"""
# pylint: disable=R0913, R0914
# disable pylint errors for too many arguments/variables
from datetime import timedelta
from date import date_floored_to_time_interval, date_ceiled_to_time_interval


def simulation_date_range_for_samples(start_times, end_times, duration, delta,
                                      start=None, end=None, delay=0):
    """ Create date range based on samples and user-specified parameters

    Keyword arguments:
    start_times -- list of datetime object(s) at start
    end_times -- list of datetime object(s) at end
    duration -- length of interval
    delta -- what to round to
    start -- specified start date
    end -- specified end date
    delay -- additional time added to interval

    Output:
    tuple with (start_time, end_time) structure
    """
    if not start_times:
        raise ValueError
    if start is not None and end is not None:
        return(date_floored_to_time_interval(start, delta),
               date_ceiled_to_time_interval(end, delta))
    min_date = start_times[0]
    max_date = min_date
    for i in range(0, len(start_times)):
        if start_times[i] < min_date:
            min_date = start_times[i]
        try:
            if end_times[i] > max_date:
                max_date = end_times[i]
        # if end_times is an empty list, don't error
        except IndexError:
            continue
    return (date_floored_to_time_interval(start or min_date, delta),
            date_ceiled_to_time_interval(end or max_date +
                                         timedelta(minutes=duration+delay),
                                         delta))
