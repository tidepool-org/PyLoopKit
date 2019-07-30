#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 16:39:23 2019

@author: annaquinlan
"""


def are_settings_valid(settings):
    """ Checks that a settings dictionary has needed properties, and
        that the values of those properties are reasonable
        (no negative insulin peaks, etc)
    """
    model = settings.get("model")
    if (any(value <= 0 or value >= 1440 for value in model)
            or model[0] > 24 if len(model) == 1 else model[1] > 120
            or model[1] > model[0] if len(model) == 2 else False
       ):
        print("Expected valid insulin model")
        return False

    if settings.get("momentum_time_interval") < 5:
        print("Expected momentum interval to be at least 5 minutes")
        return False

    if (settings.get("suspend_threshold")
            and settings.get("suspend_threshold") < 50
       ):
        print("Expected suspend threshold >= 50")
        return False

    if any(
            absorption <= 0 for absorption in settings.get(
                "default_absorption_times"
            )
       ):
        print("Expected positive absorption time")
        return False

    if (settings.get("max_basal_rate") <= 0
            or settings.get("max_basal_rate") > 35
       ):
        print("Expected maximum basal rate greater than 0 and less than 35")
        return False

    if (settings.get("max_bolus") <= 0
            or settings.get("max_bolus") > 30
       ):
        print("Expected maximum bolus greater than 0 and less than 30")
        return False

    return True
