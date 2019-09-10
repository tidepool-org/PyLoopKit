#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 18:54:26 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/GlucoseKit/GlucoseStore.swift
"""
# pylint: disable=R0913, W0612
from datetime import timedelta

from pyloopkit.loop_math import filter_date_range
from pyloopkit.glucose_math import linear_momentum_effect, counteraction_effects


def get_recent_momentum_effects(
        glucose_starts, glucose_values,
        start_date,
        now_date,
        momentum_data_interval=15,
        delta=5,
        display_list=None,
        provenances=None
        ):
    """ Get glucose momentum effects

    Arguments:
    glucose_starts -- list of datetime objects of times of glucose values
    glucose_values -- list of glucose values (unit: mg/dL)

    start_date -- date to start calculating momentum effects
    now_date -- the date to assume as the "now" time (aka datetime.now())

    momentum_data_interval -- time to generate momentum effects out to (mins)
    delta -- time between blood glucose measurements (mins)

    display_list -- list of display_only booleans
    provenances -- list of provenances (Strings)

    Output:
    Momentum effects in format (date_of_effect, value_of_effect)
    """
    assert len(glucose_starts) == len(glucose_values),\
        "expected input shapes to match"

    if not glucose_starts or not start_date:
        return ([], [])

    (filtered_dates,
     ends,
     filtered_values) = filter_date_range(
         glucose_starts,
         [],
         glucose_values,
         now_date - timedelta(minutes=momentum_data_interval),
         None
         )

    if not display_list:
        display_list = [False for i in filtered_dates]
    if not provenances:
        provenances = ["PyLoop" for i in filtered_dates]

    effects = linear_momentum_effect(
        filtered_dates, filtered_values, display_list, provenances,
        momentum_data_interval,
        delta
        )

    return effects


def get_counteraction_effects(
        glucose_starts, glucose_values,
        start_date,
        effect_starts, effect_values,
        display_list=None,
        provenances=None
        ):
    """ Get counteraction effects

    Arguments:
    glucose_starts -- list of datetime objects of times of glucose values
    glucose_values -- list of glucose values (unit: mg/dL)

    start_date -- date to begin using glucose data (datetime)

    effect_dates -- list of datetime objects associated with a glucose effect
    effect_values -- list of values associated with a glucose effect

    display_list -- list of display_only booleans
    provenances -- list of provenances (Strings)

    Output:
    Counteraction effects in form (effect start, effect end, effect value)
    """
    assert len(glucose_starts) == len(glucose_values),\
        "expected input shapes to match"

    if not glucose_starts or not start_date:
        return ([], [])

    (filtered_starts,
     ends,
     filtered_values) = filter_date_range(
         glucose_starts,
         [],
         glucose_values,
         start_date,
         None
         )

    if not display_list:
        display_list = [False for i in filtered_starts]
    if not provenances:
        provenances = ["PyLoop" for i in filtered_starts]

    counteractions = counteraction_effects(
        filtered_starts, filtered_values, display_list, provenances,
        effect_starts, effect_values
        )

    return counteractions
