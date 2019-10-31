#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  3 15:36:31 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/CarbKit/CarbStatus.swift
"""
# pylint: disable=R0913, R0914
from datetime import timedelta

from pyloopkit.date import time_interval_since
from pyloopkit import carb_math


def dynamic_carbs_on_board_helper(
        carb_start,
        carb_value,
        absorption_dict,
        observed_timeline,
        at_date,
        default_absorption_time,
        delay,
        delta,
        carb_absorption_time=None
        ):
    """
    Find partial COB for a particular carb entry *dynamically*

    Arguments:
    carb_start -- time of carb entry (datetime objects)
    carb_value -- grams of carbs eaten

    absorption_dict -- list of absorption information
                       (computed via map_)
    observed_timeline -- list of carb absorption info at various times
                         (computed via map_)

    at_date -- date to calculate the glucose effect (datetime object)

    default_absorption_time -- absorption time to use for unspecified
                               carb entries

    delay -- the time to delay the carb effect
    carb_absorption_time -- time carbs will take to absorb (mins)

    Output:
    Carbohydrate value (g)
    """

    # We have to have absorption info for dynamic calculation
    if (at_date < carb_start - timedelta(minutes=delta)
            or not absorption_dict
       ):
        return carb_math.carbs_on_board_helper(
            carb_start,
            carb_value,
            at_date,
            default_absorption_time,
            delay,
            carb_absorption_time
            )

    # Less than minimum observed; calc based on min absorption rate
    if observed_timeline and None in observed_timeline[0]:
        time = time_interval_since(at_date, carb_start) / 60 - delay
        estimated_date_duration = (
            time_interval_since(
                absorption_dict[5],
                absorption_dict[4]
                ) / 60
            + absorption_dict[6]
        )
        return carb_math.linear_unabsorbed_carbs(
            absorption_dict[2],
            time,
            estimated_date_duration
            )

    if (not observed_timeline  # no absorption was observed (empty list)
            or not observed_timeline[len(observed_timeline)-1]
            or at_date > observed_timeline[len(observed_timeline) - 1][1]
       ):
        # Predict absorption for remaining carbs, post-observation
        total = absorption_dict[3]  # these are the still-unabsorbed carbs
        time = time_interval_since(at_date, absorption_dict[5]) / 60
        absorption_time = absorption_dict[6]

        return carb_math.linear_unabsorbed_carbs(
            total,
            time,
            absorption_time
        )

    # There was observed absorption
    total = carb_value
    def partial_absorption(dict_):
        if dict_[1] > at_date:
            return 0
        return dict_[2]

    for dict_ in observed_timeline:
        total -= partial_absorption(dict_)

    return max(
        total,
        0
        )


def dynamic_absorbed_carbs(
        carb_start,
        carb_value,
        absorption_dict,
        observed_timeline,
        at_date,
        carb_absorption_time,
        delay,
        delta,
        ):
    """
    Find partial absorbed carbs for a particular carb entry *dynamically*

    Arguments:
    carb_start -- time of carb entry (datetime objects)
    carb_value -- grams of carbs eaten

    absorption_dict -- list of absorption information
                       (computed via map_)
    observed_timeline -- list of carb absorption info at various times
                         (computed via map_)

    at_date -- date to calculate the glucose effect (datetime object)

    carb_absorption_time -- time carbs will take to absorb (mins)

    delay -- the time to delay the carb effect

    Output:
    Carbohydrate value (g)
    """

    # We have to have absorption info for dynamic calculation
    if (at_date < carb_start
            or not absorption_dict
       ):
        return carb_math.absorbed_carbs(
            carb_start,
            carb_value,
            carb_absorption_time,
            at_date,
            delay,
            )
    # Less than minimum observed; calc based on min absorption rate
    if observed_timeline and None in observed_timeline[0]:
        time = time_interval_since(at_date, carb_start) / 60 - delay
        estimated_date_duration = (
            time_interval_since(
                absorption_dict[5],
                absorption_dict[4]
                ) / 60
            + absorption_dict[6]
        )
        return carb_math.linearly_absorbed_carbs(
            absorption_dict[2],
            time,
            estimated_date_duration
            )

    if (not observed_timeline  # no absorption was observed (empty list)
            or not observed_timeline[len(observed_timeline)-1]
            or at_date > observed_timeline[len(observed_timeline) - 1][1]
       ):
        # Predict absorption for remaining carbs, post-observation
        total = absorption_dict[3]  # these are the still-unabsorbed carbs
        time = time_interval_since(at_date, absorption_dict[5]) / 60
        absorption_time = absorption_dict[6]

        return absorption_dict[1] + carb_math.linearly_absorbed_carbs(
            total,
            time,
            absorption_time
        )

    sum_ = 0

    # There was observed absorption
    def filter_dates(sub_timeline):
        return sub_timeline[0] + timedelta(minutes=delta) <= at_date

    before_timelines = list(filter(filter_dates, observed_timeline))

    if before_timelines:
        last = before_timelines.pop()
        observation_interval = (last[1] - last[0]).total_seconds()
        if observation_interval > 0:
            # find the minutes of overlap between calculation_interval
            # and observation_interval
            calculation_interval = (
                last[1] - min(
                    last[0],
                    at_date
                    )
                ).total_seconds()
            sum_ += (calculation_interval
                     / observation_interval
                     * last[2]
                     )

    for dict_ in before_timelines:
        sum_ += dict_[2]

    return min(
        sum_,
        absorption_dict[0]
        )
