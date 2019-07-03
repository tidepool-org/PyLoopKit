#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  3 15:36:31 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/CarbKit/CarbStatus.swift
"""
# pylint: disable=R0913
from datetime import timedelta

from date import time_interval_since
import carb_math

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

    if (at_date < carb_start - timedelta(minutes=delta)
            or not absorption_dict
       ):


        # We have to have absorption info for dynamic calculation
        return carb_math.carbs_on_board_helper(
            carb_start,
            carb_value,
            at_date,
            default_absorption_time,
            delay,
            carb_absorption_time
            )
    if not observed_timeline:
        # Less than minimum observed; calc based on min absorption rate
        time = time_interval_since(at_date, carb_start) / 60 - delay

        return carb_math.linear_unabsorbed_carbs(
            carb_value,
            time,
            carb_absorption_time or default_absorption_time
            )

    if (not observed_timeline[len(observed_timeline)-1]
            or at_date > observed_timeline[len(observed_timeline) - 1]
       ):
        # Predict absorption for remaining carbs, post-observation
        total = absorption_dict[3]  # these are the still-unabsorbed carbs
        time = time_interval_since(at_date, absorption_dict[4]) / 60
        absorption_time = absorption_dict[6]

        return carb_math.linear_unabsorbed_carbs(
            total,
            time,
            absorption_time
        )

    # Observed absorption
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
