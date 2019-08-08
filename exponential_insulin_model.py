#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 16:04:11 2019

@author: annaquinlan

https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/InsulinKit/
ExponentialInsulinModel.swift
"""
# pylint: disable=C0103
import math


def percent_effect_remaining(time, action_duration, peak_activity_time):
    """ Returns the percentage of total insulin effect remaining at a specified
        interval after delivery; aka insulin on board (IOB)

        This model allows us to specify time of peak activity, as well as
        duration, and provides activity and IOB decay functions

    Arguments:
    time -- the minutes after insulin delivery (it can be negative)
    action_duration -- the total duration on insulin activity (DIA)
    peak_activity_time -- the time (in minutes) of the peak of insulin activity
                          from dose

    Output:
    The percentage of total insulin effect remaining
    """

    if time <= 0:
        return 1
    if time > action_duration:
        return 0

    tau = (peak_activity_time * (1 - peak_activity_time / action_duration) /
           (1 - 2 * peak_activity_time / action_duration)
           )
    a = 2 * tau / action_duration
    S = 1 / (1 - a + (1 + a) * math.exp(-action_duration / tau))

    return 1 - S * (1 - a) * ((pow(time, 2) / (tau * action_duration * (1 - a))
                               - time / tau - 1) * math.exp(-time / tau) + 1)
