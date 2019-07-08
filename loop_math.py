#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 10:40:48 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
            57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/LoopMath.swift
"""
# pylint: disable=R0913, R0914, C0200, R0912, R0915, W0102
# disable pylint errors for too many arguments/variables
from datetime import timedelta

from date import (date_floored_to_time_interval,
                  date_ceiled_to_time_interval, time_interval_since)


def predict_glucose(starting_date, starting_glucose,
                    momentum_dates=[], momentum_values=None,
                    carb_effect_dates=[], carb_effect_values=None,
                    insulin_effect_dates=[], insulin_effect_values=None,
                    correction_effect_dates=[], correction_effect_values=None
                    ):
    """ Calculates a timeline of predicted glucose values
        from a variety of effects timelines.

    Each effect timeline:
     - Is given equal weight (exception: momentum effect timeline)
     - Can be of arbitrary size and start date
     - Should be in ascending order
     - Should have aligning dates with any overlapping timelines to ensure
       a smooth result

    Parameters:
    starting_date -- time of starting_glucose (datetime object)
    starting_glucose -- glucose value to use in predictions

    momentum_dates -- times of calculated momentums (datetime)
    momentum_values -- values (mg/dL) of momentums

    carb_effect_dates -- times of carb effects (datetime)
    carb_effect -- values (mg/dL) of effects from carbs

    insulin_effect_dates -- times of insulin effects (datetime)
    insulin_effect -- values (mg/dL) of effects from insulin

    correction_effect_dates -- times of retrospective effects (datetime)
    correction_effect -- values (mg/dL) retrospective glucose effects

    Output:
    Glucose predictions in form (prediction_times, prediction_glucose_values)
    """
    if momentum_dates:
        assert len(momentum_dates) == len(momentum_values),\
            "expected input shapes to match"

    if carb_effect_dates:
        assert len(carb_effect_dates) == len(carb_effect_values),\
            "expected input shapes to match"

    if insulin_effect_dates:
        assert len(insulin_effect_dates) == len(insulin_effect_values),\
            "expected input shapes to match"

    if correction_effect_dates:
        assert len(correction_effect_dates) == len(correction_effect_values),\
            "expected input shapes to match"

    # if we didn't get any effect data, we won't predict the glucose
    if (not carb_effect_dates and
            not insulin_effect_dates and
            not correction_effect_dates
       ):
        return ([], [])

    merged_dates = list(
        dict.fromkeys(
            momentum_dates
            + carb_effect_dates
            + insulin_effect_dates
            + correction_effect_dates
        )
    )
    merged_values = [0 for i in merged_dates]

    # TODO: is there a way to not have to repeat this code
    # for every effect value type?
    # possibly as a tensor where dates are the same?
    if carb_effect_dates:
        previous_effect_value = carb_effect_values[0] or 0
        for i in range(0,
                       len(carb_effect_dates)
                       ):
            value = carb_effect_values[i]
            list_index = merged_dates.index(carb_effect_dates[i])
            merged_values[list_index] = (
                value
                - previous_effect_value
            )

            previous_effect_value = value

    if insulin_effect_dates:
        previous_effect_value = insulin_effect_values[0] or 0
        for i in range(0,
                       len(insulin_effect_dates)
                       ):
            value = insulin_effect_values[i]
            list_index = merged_dates.index(insulin_effect_dates[i])
            merged_values[list_index] = (
                merged_values[list_index]
                + value
                - previous_effect_value
            )

            previous_effect_value = value

    if correction_effect_dates:
        previous_effect_value = correction_effect_values[0] or 0
        for i in range(0,
                       len(correction_effect_dates)
                       ):
            value = insulin_effect_values[i]
            list_index = merged_dates.index(correction_effect_dates[i])
            merged_values[list_index] = (
                merged_values[list_index]
                + value
                - previous_effect_value
            )

            previous_effect_value = value

    # Blend the momentum effect linearly into the summed effect list
    if len(momentum_dates) > 1:
        previous_effect_value = momentum_values[0]

        # The blend begins delta minutes after after the last glucose (1.0)
        # and ends at the last momentum point (0.0)
        # We're assuming the first one occurs on/before the starting glucose
        blend_count = len(momentum_dates) - 2
        time_delta = time_interval_since(
            momentum_dates[1],
            momentum_dates[0]
            ) / 60
        # The difference between the first momentum value
        # and the starting glucose value
        momentum_offset = time_interval_since(
            starting_date,
            momentum_dates[0]
            ) / 60

        blend_slope = 1 / blend_count
        blend_offset = (momentum_offset
                        / time_delta
                        * blend_slope
                        )

        for i in range(0, len(momentum_dates)):
            value = momentum_values[i]
            date = momentum_dates[i]
            merge_index = merged_dates.index(date)

            effect_value_change = value - previous_effect_value

            split = min(1,
                        max(0,
                            (len(momentum_dates) - i)
                            / blend_count
                            - blend_slope
                            + blend_offset
                            )
                        )
            effect_blend = (
                (1 - split)
                * merged_values[merge_index]
            )
            momentum_blend = split * effect_value_change

            merged_values[merge_index] = effect_blend + momentum_blend
            previous_effect_value = value

    predicted_dates = [starting_date]
    predicted_values = [starting_glucose]

    for i in range(0, len(merged_dates)):
        if merged_dates[i] > starting_date:
            last_value = predicted_values[-1]

            predicted_dates.append(
                merged_dates[i]
            )
            predicted_values.append(
                last_value
                + merged_values[i]
            )

    return (predicted_dates, predicted_values)


def simulation_date_range_for_samples(start_times, end_times, duration, delta,
                                      start=None, end=None, delay=0):
    """ Create date range based on samples and user-specified parameters

    Arguments:
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
               date_ceiled_to_time_interval(end, delta)
               )

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
            date_ceiled_to_time_interval(end or max_date
                                         + timedelta(minutes=duration+delay),
                                         delta)
            )
