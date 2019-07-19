#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 16:04:15 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/Loop/blob/
8c1dfdba38fbf6588b07cee995a8b28fcf80ef69/Loop/Managers/LoopDataManager.swift
"""
# pylint: disable=R0913, R0914, W0105
from datetime import datetime, timedelta, time
import json
import os

from date import time_interval_since
from dose_store import get_glucose_effects
from glucose_store import (get_recent_momentum_effects,
                           get_counteraction_effects)
from loop_math import combined_sums, decay_effect, subtracting
from carb_store import get_carb_glucose_effects, get_carbs_on_board


def update_retrospective_glucose_effect(
        glucose_dates, glucose_values,
        carb_effect_dates, carb_effect_values,
        counteraction_starts, counteraction_ends, counteraction_values,
        recency_interval,
        retrospective_correction_grouping_interval,
        now_time,
        effect_duration=60,
        delta=5
        ):
    """
    Generate an effect based on how large the discrepancy is between the
    current glucose and its predicted value.

    Arguments:
    glucose_dates -- time of glucose value (datetime)
    glucose_values -- value at the time of glucose_date

    carb_effect_dates -- date the carb effects occur at (datetime)
    carb_effect_values -- value of carb effect

    counteraction_starts -- start times for counteraction effects
    counteraction_ends -- end times for counteraction effects
    counteraction_values -- values of counteraction effects

    recency_interval -- amount of time since a given date that data should be
                        considered valid
    retrospective_correction_grouping_interval -- interval over which to
        aggregate changes in glucose for retrospective correction

    now_time -- the time the loop is being run at
    effect_duration -- the length of time to calculate the retrospective
                       glucose effect out to
    delta -- time interval between glucose values (mins)

    Output:
    Retrospective glucose effect information
    """
    assert len(glucose_dates) == len(glucose_values),\
        "expected input shapes to match"

    assert len(carb_effect_dates) == len(carb_effect_values),\
        "expected input shapes to match"

    assert len(counteraction_starts) == len(counteraction_ends)\
        == len(counteraction_values), "expected input shapes to match"

    if not carb_effect_dates or not glucose_dates:
        return ([], [])

    (discrepancy_starts, discrepancy_values) = subtracting(
        counteraction_starts, counteraction_ends, counteraction_values,
        carb_effect_dates, [], carb_effect_values,
        delta
        )

    retrospective_glucose_discrepancies_summed = combined_sums(
        discrepancy_starts, discrepancy_starts, discrepancy_values,
        retrospective_correction_grouping_interval * 1.01
        )

    # Our last change should be recent, otherwise clear the effects
    if (time_interval_since(
            retrospective_glucose_discrepancies_summed[1][-1],
            now_time) / 60
            > recency_interval
       ):
        return ([], [])

    discrepancy_time = max(
        0,
        retrospective_correction_grouping_interval
        )

    velocity = (
        retrospective_glucose_discrepancies_summed[2][-1]
        / discrepancy_time
        )

    return decay_effect(
        glucose_dates[-1], glucose_values[-1],
        velocity,
        effect_duration
        )
