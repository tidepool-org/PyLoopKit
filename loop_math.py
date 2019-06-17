#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 10:40:48 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
            57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/LoopMath.swift
"""
from date import date_floored_to_time_interval, date_ceiled_to_time_interval
from datetime import timedelta


def simulation_date_range_for_samples(samples, duration, delta, start=None,
                                      end=None, delay=0):
    if len(samples) <= 0:
        raise ValueError
    if start is not None and end is not None:
        return(date_floored_to_time_interval(start, delta),
               date_ceiled_to_time_interval(end, delta))
    else:
        min_date = samples[0].start_date
        max_date = min_date
        for sample in samples:
            if sample.start_date < min_date:
                min_date = sample.start_date
            try:
                if sample.end_date > max_date:
                    max_date = sample.end_date
            # if the object passed has no end_date property, don't error
            except AttributeError:
                pass
        return (date_floored_to_time_interval(start or min_date, delta),
                date_ceiled_to_time_interval(end or max_date +
                                             timedelta(minutes=duration+delay),
                                             delta))
