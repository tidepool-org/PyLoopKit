#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 18:54:26 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/GlucoseKit/GlucoseStore.swift
"""
from datetime import timedelta

from loop_math import filter_date_range
from glucose_math import linear_momentum_effect


def get_recent_momentum_effects(
        glucose_starts, glucose_values,
        start_date,
        momentum_data_interval=15,
        delta=5,
        display_list=None,
        provenances=None
        ):
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
        start_date - timedelta(minutes=momentum_data_interval),
        None
        )

    if not display_list:
        display_list = [False for i in filtered_starts]
    if not provenances:
        provenances = ["PyLoop" for i in filtered_starts]

    effects = linear_momentum_effect(
        filtered_starts, filtered_values, display_list, provenances,
        momentum_data_interval,
        delta
        )

    return effects
