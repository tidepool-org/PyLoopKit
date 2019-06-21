#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 09:57:26 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/InsulinKit/DoseEntry.swift
"""
from date import time_interval_since


def net_basal_units(type_, value, start, end, scheduled_basal_rate):
    """ Find the units of insulin delivered, net of any scheduled basal rate
        (if dose is a temp basal)

    Arguments:
    type_ -- type of dose (basal, bolus, suspend, etc)
    value -- if bolus: amount given, if temp basal: temp rate (U/hr)
    start -- datetime object representing start of dose
    end -- datetime object representing end of dose

    Output:
    Bolus amount (if a bolus), or basal units given, net of whatever the
    schedule basal is
    """
    if type_ == "Bolus":
        return value
    hours_ = hours(end, start)
    return (value - scheduled_basal_rate) * hours_


def hours(start_date, end_date):
    """ Find hours between two dates """
    return abs(time_interval_since(end_date, start_date))/60/60  # secs -> hrs
