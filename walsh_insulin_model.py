#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 15:08:22 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/InsulinKit/
WalshInsulinModel.swift
"""


def walsh_percent_effect_remaining(minutes, action_duration):
    """ Give percent of insulin remaining for IOB calculations.
        This curve is only included for the purposes of running glucose
        activity tests

        Arguments:
        minutes -- minutes after insulin delivery
        dia -- duration of insulin action, in hours
    """
    if minutes <= 0:
        return 1
    if minutes >= action_duration * 60:
        return 0

    dia = round(action_duration)
    if dia < 3:
        dia = 3
    elif dia > 6:
        dia = 6

    minutes = minutes * dia / action_duration

    if dia == 3:
        return -3.2030e-9 * pow(minutes, 4) + 1.354e-6 * pow(minutes, 3)\
            - 1.759e-4 * pow(minutes, 2) + 9.255e-4 * minutes + 0.99951
    if dia == 4:
        return -3.310e-10 * pow(minutes, 4) + 2.530e-7 * pow(minutes, 3)\
            - 5.510e-5 * pow(minutes, 2) - 9.086e-4 * minutes + 0.99950
    if dia == 5:
        return -2.950e-10 * pow(minutes, 4) + 2.320e-7 * pow(minutes, 3)\
            - 5.550e-5 * pow(minutes, 2) + 4.490e-4 * minutes + 0.99300
    if dia == 6:
        return -1.493e-10 * pow(minutes, 4) + 1.413e-7 * pow(minutes, 3)\
            - 4.095e-5 * pow(minutes, 2) + 6.365e-4 * minutes + 0.99700

    raise RuntimeError
