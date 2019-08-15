#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 09:21:47 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/GlucoseEffect.swift
"""


class GlucoseEffect:
    """ Constructs a glucose effect

    Attributes:
    start_date -- date and time of the effect
    quantity -- glucose value (mg/dL)
    """
    def __init__(self, start_date, quantity):
        self.start_date = start_date
        self.quantity = quantity

    def __lt__(self, other):
        return self.start_date < other.start_date
