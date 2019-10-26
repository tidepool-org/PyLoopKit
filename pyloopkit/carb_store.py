#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 15:31:31 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/CarbKit/CarbStore.swift
"""
# pylint: disable=R0913, R0914
from datetime import timedelta

from pyloopkit.carb_math import (filter_date_range_for_carbs, map_, carb_glucose_effects,
                       dynamic_glucose_effects, dynamic_carbs_on_board,
                       carbs_on_board)


def get_carb_glucose_effects(
        carb_dates, carb_values, absorption_times,
        at_date,
        effect_starts, effect_ends, effect_values,
        carb_ratio_starts, carb_ratios,
        sensitivity_starts, sensitivity_ends, sensitivity_values,
        default_absorption_times,
        absorption_time_overrun=1.5,
        delay=10,
        delta=5,
        end_date=None
        ):
    """ Retrieve a timeline of effect on blood glucose from carbohydrates

    Arguments:
    carb_dates -- list of times of carb entry (datetime objects)
    carb_values -- list of grams of carbs eaten
    absorption_times -- list of lengths of absorption times (mins)

    at_date -- the time to calculate the effect at (datetime object)

    effect_starts -- list of start times of carb effect (datetime objects)
    effect_ends -- list of end times of carb effect (datetime objects)
    effect_values -- list of glucose velocities (mg/dL)

    carb_ratio_starts -- list of start times of carb ratios (time objects)
    carb_ratios -- list of carb ratios (g/U)

    sensitivity_starts -- list of time objects of start times of
                          given insulin sensitivity values
    sensitivity_ends -- list of time objects of start times of
                        given insulin sensitivity values
    sensitivity_values -- list of sensitivities (mg/dL/U)

    default_absorption_time -- absorption time to use for unspecified
                               carb entries

    absorption_time_overrun -- multiplier to determine absorption time
                               from the specified absorption time

    delay -- the time to delay the carb effect
    delta -- time interval between glucose values

    end_date -- date to end calculation of glucose effects

    Output:
    An array of effects in chronological order
    """
    assert len(carb_dates) == len(carb_values) == len(absorption_times),\
        "expected input shapes to match"

    assert len(effect_starts) == len(effect_ends) == len(effect_values),\
        "expected input shapes to match"

    if not carb_dates:
        return ([], [])

    maximum_absorption_time_interval = default_absorption_times[2] * 2

    # To know glucose effects at the requested start date, we need to fetch
    # samples that might still be absorbing
    food_start = at_date - timedelta(minutes=maximum_absorption_time_interval)

    filtered_carbs = filter_date_range_for_carbs(
        carb_dates, carb_values, absorption_times,
        food_start,
        end_date
        )

    # if we have counteraction effects, generate our carb glucose effects
    # with a dynamic model
    if effect_starts and effect_starts[0]:
        (absorption_results,
         timelines
         ) = map_(
             *filtered_carbs,
             effect_starts, effect_ends, effect_values,
             carb_ratio_starts, carb_ratios,
             sensitivity_starts, sensitivity_ends, sensitivity_values,
             absorption_time_overrun,
             default_absorption_times[1],
             delay,
             delta
             )[0:2]

        effects = dynamic_glucose_effects(
            *filtered_carbs,
            absorption_results, timelines,
            carb_ratio_starts, carb_ratios,
            sensitivity_starts, sensitivity_ends, sensitivity_values,
            default_absorption_times[1],
            delay,
            delta,
            start=at_date,
            end=end_date,
            scaler=1.7
            )
    # otherwise, use a static model
    else:
        effects = carb_glucose_effects(
            *filtered_carbs,
            carb_ratio_starts, carb_ratios,
            sensitivity_starts, sensitivity_ends, sensitivity_values,
            default_absorption_times[1],
            delay,
            delta,
            at_date,
            end_date
            )

    assert len(effects[0]) == len(effects[1]), "expected output shape to match"

    return effects


def get_carbs_on_board(
        carb_dates, carb_values, absorption_times,
        at_date,
        effect_starts, effect_ends, effect_values,
        carb_ratio_starts, carb_ratios,
        sensitivity_starts, sensitivity_ends, sensitivity_values,
        default_absorption_times,
        absorption_time_overrun=1.5,
        delay=10,
        delta=5,
        end_date=None
        ):
    """ Retrieves the COB at a time, or a timeline of COB

    Arguments:
    carb_dates -- list of times of carb entry (datetime objects)
    carb_values -- list of grams of carbs eaten
    absorption_times -- list of lengths of absorption times (mins)

    at_date -- the time to calculate the COB at (datetime object)

    effect_starts -- list of start times of carb effect (datetime objects)
    effect_ends -- list of end times of carb effect (datetime objects)
    effect_values -- list of glucose velocities (mg/dL)

    carb_ratio_starts -- list of start times of carb ratios (time objects)
    carb_ratios -- list of carb ratios (g/U)

    sensitivity_starts -- list of time objects of start times of
                          given insulin sensitivity values
    sensitivity_ends -- list of time objects of start times of
                        given insulin sensitivity values
    sensitivity_values -- list of sensitivities (mg/dL/U)

    default_absorption_times -- list absorption times to use for unspecified
                               carb entries in format [fast, medium, slow]

    absorption_time_overrun -- multiplier to determine absorption time
                               from the specified absorption time

    delay -- the time to delay the COB
    delta -- time interval between glucose values

    end_date -- date to end calculation of COB

    Output:
    COB timeline
    """
    assert len(carb_dates) == len(carb_values) == len(absorption_times),\
        "expected input shapes to match"

    assert len(effect_starts) == len(effect_ends) == len(effect_values),\
        "expected input shapes to match"

    if not carb_dates:
        return ([], [])

    start_date = at_date - timedelta(minutes=delta)

    maximum_absorption_time_interval = default_absorption_times[2] * 2

    # To know COB at the requested start date, we need to fetch samples that
    # might still be absorbing
    food_start = start_date - timedelta(
        minutes=maximum_absorption_time_interval
    )

    filtered_carbs = filter_date_range_for_carbs(
        carb_dates, carb_values, absorption_times,
        food_start,
        end_date
        )

    # If we have counteraction effects, use a dynamic model
    if (effect_starts and effect_starts[0]
            and carb_ratio_starts
            and sensitivity_starts
       ):
        (absorption_results,
         timelines
         ) = map_(
             *filtered_carbs,
             effect_starts, effect_ends, effect_values,
             carb_ratio_starts, carb_ratios,
             sensitivity_starts, sensitivity_ends, sensitivity_values,
             absorption_time_overrun,
             default_absorption_times[1],
             delay,
             delta
             )[0:2]

        cob_data = dynamic_carbs_on_board(
            *filtered_carbs,
            absorption_results, timelines,
            default_absorption_times[1],
            delay,
            delta,
            start=start_date,
            end=end_date,
            scaler=1.5
            )
    # otherwise, use a static model
    else:
        cob_data = carbs_on_board(
            *filtered_carbs,
            default_absorption_times[1],
            delay,
            delta,
            start=start_date,
            end=end_date
            )

    return cob_data
