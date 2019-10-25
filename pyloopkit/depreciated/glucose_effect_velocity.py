#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 09:23:51 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/GlucoseEffectVelocity.swift
"""


class GlucoseEffectVelocity:
    """ Constructs a velocity of a glucose effect

    Attributes:
    start_date -- start date and time of the effect
    end_date -- end date and time of the effect
    quantity -- glucose value (mg/dL)
    """
    def __init__(self, start_date, end_date, quantity):
        self.start_date = start_date
        self.end_date = end_date
        self.quantity = quantity
