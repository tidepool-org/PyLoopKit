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
    """ Converts a continuous, chronological sequence of reservoir values
        to a sequence of doses
    Runtime: O(n)

    Arguments:
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


def is_continuous(reservoir_dates, unit_volumes, start, end,
                  maximum_duration):
    """ Whether a span of chronological reservoir values is considered
        continuous and therefore reliable.

    Reservoir values of 0 are automatically considered unreliable due to
    the assumption that an unknown amount of insulin can be delivered after
    the 0 marker.

    Arguments:
    reservoir_dates -- list of datetime objects that correspond by index to
                        unit_volumes
    unit_volumes -- volume of reservoir in units, corresponds by index to
                    reservoir_dates
    start -- datetime object that is start of the interval which to validate
             continuity
    end -- datetime object that is end of the interval which to validate
             continuity
    maximum_duration -- the maximum interval to consider reliable for a
                        reservoir-derived dose

    Variable names:
    start_date -- the beginning of the interval in which to validate
                   continuity
    end_date -- the end of the interval in which to validate continuity

    Outputs:
    Whether the reservoir values meet the critera for continuity
    """
    try:
        first_date_value = reservoir_dates[0]
        first_volume_value = unit_volumes[0]
    except IndexError:
        return False

    start_date = start
    # The first value has to be at least as old as the start date
    # as a reference point.
    if first_date_value > start_date:
        return False

    last_date_value = first_date_value
    last_volume_value = first_volume_value

    for i in range(0, len(unit_volumes)):
        # ! no end_date property...
        # Volume and interval validation only applies for values in
        # the specified range
        if reservoir_dates[i] < start_date or reservoir_dates[i] > end:
            last_date_value = reservoir_dates[i]
            last_volume_value = unit_volumes[i]
            print("line 112")
            continue
        # We can't trust 0. What else was delivered?
        if unit_volumes[i] <= 0:
            print("line 116")
            return False
        # Rises in reservoir volume indicate a rewind + prime, and primes
        # can be easily confused with boluses.
        # Small rises (1 U) can be ignored as they're indicative of a
        # mixed-precision sequence.
        if unit_volumes[i] > last_volume_value + 1:
            print("line 123")
            return False
        # Ensure no more than the maximum interval has passed
        if (time_interval_since(reservoir_dates[i], last_date_value)/60
                > maximum_duration):
            print("line 128")
            return False

        last_date_value = reservoir_dates[i]
        last_volume_value = unit_volumes[i]

    print("\n")
    return True
