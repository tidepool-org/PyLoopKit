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


def predict_glucose(
        starting_date, starting_glucose,
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

    assert len(predicted_dates) == len(predicted_values),\
        "expected output shapes to match"
    return (predicted_dates, predicted_values)


def decay_effect(
        glucose_date, glucose_value,
        rate,
        duration,
        delta=5
        ):
    """ Calculates a timeline of glucose effects by applying a
        linear decay to a rate of change.

    Arguments:
    glucose_date -- time of glucose value (datetime)
    glucose_value -- value at the time of glucose_date
    rate -- the glucose velocity
    duration -- the duration the effect should continue before ending
    delta -- the time differential for the returned values

    Output:
    Glucose effects in format (effect_date, effect_value)
    """
    (start_date,
     end_date
     ) = simulation_date_range_for_samples(
         [glucose_date],
         [],
         duration,
         delta
         )

    # The starting rate, which we will decay to 0 over the specified duration
    intercept = rate
    last_value = glucose_value
    effect_dates = [start_date]
    effect_values = [glucose_value]

    date = decay_start_date = start_date + timedelta(minutes=delta)
    slope = (-intercept
             / (duration - delta)
             )

    while date < end_date:
        value = (
            last_value
            + (intercept
               + slope * time_interval_since(
                   date, decay_start_date
                   )
               / 60) * delta
                )

        effect_dates.append(date)
        effect_values.append(value)

        last_value = value
        date = date + timedelta(minutes=delta)

    assert len(effect_dates) == len(effect_values),\
        "expected output shapes to match"

    return (effect_dates, effect_values)


def simulation_date_range_for_samples(
        start_times,
        end_times,
        duration,
        delta,
        start=None,
        end=None,
        delay=0
        ):
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


def subtracting(starts, ends, values,
                other_starts, other_ends, other_values,
                effect_interval
                ):
    """ Subtracts an array of glucose effects with uniform intervals and
        no gaps from the collection of effect changes, which may not
        have uniform intervals.

    Parameters:
    starts -- start times of effect that is subtracted-from (datetime)
    ends -- end times of effect that is subtracted-from (datetime)
    values -- values of effect that is subtracted-from (datetime)

    other_starts -- start times of the effect to subtract (datetime)
    other_ends -- end times of the effect to subtract (datetime)
    other_values -- values of the effect to subtract

    Output:
    The resulting array of glucose effects in the form
    (start_times, end_times, values)
    """
    assert len(starts) == len(ends) == len(values),\
        "expected input shapes to match"
    assert len(other_starts) == len(other_values),\
        "expected input shapes to match"
    # Trim both collections to match
    (other_starts,
     other_ends,
     other_values
     ) = filter_date_range(
         other_starts, other_ends, other_values,
         ends[0],
         None
         )
    (starts,
     ends,
     values
     ) = filter_date_range(
         starts, ends, values,
         other_starts[0],
         None
         )

    (subtracted_starts,
     subtracted_values
     ) = ([], [])

    previous_other_effect_value = other_values[0]
    effect_index = 0

    for i in range(1, len(other_starts)):
        if effect_index >= len(starts):
            break

        other_effect_value = other_values[i]
        other_effect_change = other_effect_value - previous_other_effect_value

        previous_other_effect_value = other_effect_value

        # Our effect array may have gaps, or have longer segments than 5 mins
        if other_ends[i] and ends[effect_index] > other_ends[i]:
            continue  # move on to next one

        if other_starts[i] and ends[effect_index] > other_starts[i]:
            continue  # move on to next one

        effect_value = values[effect_index]
        effect_value_matching_other_effect_interval = (
            effect_value
            * effect_interval
        )

        subtracted_starts.append(
            ends[effect_index]
        )
        subtracted_values.append(
            effect_value_matching_other_effect_interval
            - other_effect_change
        )

        effect_index += 1

    # if we have run out of other_effect items,
    # we assume the other_effect_change remains zero
    for i in range(effect_index, len(starts)):
        effect_value = values[i]
        effect_value_matching_other_effect_interval = (
            effect_value
            * effect_interval
        )

        subtracted_starts.append(
            ends[i]
        )
        subtracted_values.append(
            effect_value_matching_other_effect_interval
        )

    assert len(subtracted_starts) == len(subtracted_values),\
        "expected output shapes to match"

    return (subtracted_starts, subtracted_values)


def filter_date_range(
        starts, ends, values,
        start_date,
        end_date
        ):
    """ Returns an array of elements filtered by the specified date range.

    Arguments:
    starts -- start dates (datetime)
    ends -- end dates (datetime)
    values -- glucose values

    start_date -- the earliest date of elements to return
    end_date -- the last date of elements to return

    Output:
    Filtered dates in format (starts, ends, values)
    """
    # ends might not necesarily be the same length as starts/values
    # because not all types have "end dates"
    assert len(starts) == len(values),\
        "expected input shapes to match"

    (filtered_starts,
     filtered_ends,
     filtered_values
     ) = ([], [], [])

    for i in range(0, len(starts)):
        if start_date and ends and ends[i] < start_date:
            continue

        if start_date and not ends and starts[i] < start_date:
            continue

        if end_date and starts[i] > end_date:
            continue

        filtered_starts.append(starts[i])
        filtered_ends.append(ends[i] if ends else None)
        filtered_values.append(values[i])

    assert len(filtered_starts) == len(filtered_ends) == len(filtered_values),\
        "expected output shapes to match"

    return (filtered_starts, filtered_ends, filtered_values)
