#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 18:04:24 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/Loop/blob/
8c1dfdba38fbf6588b07cee995a8b28fcf80ef69/Loop/Managers/LoopDataManager.swift
"""
# pylint: disable=R0913, R0914, C0200


def filter_date_range_for_doses(
        types, starts, ends, values, scheduled_basals,
        start_date,
        end_date
        ):
    """ Returns an array of elements filtered by the specified date range.

    Arguments:
    types -- String of type of dose (basal, bolus, etc)
    starts -- start dates (datetime)
    ends -- end dates (datetime)
    values -- glucose values
    scheduled_basals -- scheduled basal rate during dose

    start_date -- the earliest date of elements to return
    end_date -- the last date of elements to return

    Output:
    Filtered dates in format (starts, ends, values)
    """
    # ends might not necesarily be the same length as starts/values
    # because not all types have "end dates"
    assert len(types) == len(starts) == len(values) == len(scheduled_basals),\
        "expected input shapes to match"

    (filtered_types,
     filtered_starts,
     filtered_ends,
     filtered_values,
     filtered_scheduled_basals
     ) = ([], [], [], [], [])

    for i in range(0, len(starts)):
        if start_date and ends and ends[i] < start_date:
            continue

        if start_date and not ends and starts[i] < start_date:
            continue

        if end_date and starts[i] > end_date:
            continue

        filtered_types.append(types[i])
        filtered_starts.append(starts[i])
        filtered_ends.append(ends[i] if ends else None)
        filtered_values.append(values[i])
        filtered_scheduled_basals.append(scheduled_basals[i])

    assert len(filtered_types) == len(filtered_starts) == len(filtered_ends)\
        == len(filtered_values) == len(filtered_scheduled_basals),\
        "expected output shapes to match"

    return (
        filtered_types,
        filtered_starts,
        filtered_ends,
        filtered_values,
        filtered_scheduled_basals
        )
