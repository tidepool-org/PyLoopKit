#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 10:29:59 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/InsulinKit/InsulinMath.swift
"""
from date import time_interval_since

MAXIMUM_RESERVOIR_DROP_PER_MINUTE = 6.5


def dose_entries(reservoir_dates, unit_volumes):
    """ Converts reservoir data to dose entries

    Keyword arguments:
    reservoir_dates -- list of datetime objects
    unit_volumes -- list of reservoir volumes (in units of insulin)

    Output:
    A tuple of lists in (dose_type (basal/bolus), start_dates, end_dates,
        insulin_values) format
    """
    assert len(reservoir_dates) > 1,\
        "expected input lists to contain two or more items"
    assert len(reservoir_dates) == len(unit_volumes),\
        "expected input shape to match"

    dose_types = []
    start_dates = []
    end_dates = []
    insulin_values = []

    previous_date = reservoir_dates[0]
    previous_unit_volume = unit_volumes[0]

    for i in range(1, len(reservoir_dates)):
        volume_drop = previous_unit_volume - unit_volumes[i]
        duration = time_interval_since(reservoir_dates[i], previous_date)/60

        if (duration > 0 and 0 <= volume_drop <=
                MAXIMUM_RESERVOIR_DROP_PER_MINUTE * duration):
            dose_types.append("tempBasal")
            start_dates.append(previous_date)
            end_dates.append(reservoir_dates[i])
            insulin_values.append(volume_drop)

        previous_date = reservoir_dates[i]
        previous_unit_volume = unit_volumes[i]

    assert len(dose_types) == len(start_dates) == len(end_dates) ==\
        len(insulin_values), "expected output shape to match"

    return (dose_types, start_dates, end_dates, insulin_values)
