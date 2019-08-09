#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 16:39:23 2019

@author: annaquinlan
"""
# pylint: disable=R0911, W0613


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

    if any(absorption <= 0 for absorption in settings.get(
                "default_absorption_times")):
        print("Expected positive absorption time")
        return False

    if (settings.get("max_basal_rate") < 0
            or settings.get("max_basal_rate") > 35
       ):
        print("Expected maximum basal rate of at least 0 and less than 35")
        return False

    if (settings.get("max_bolus") < 0
            or settings.get("max_bolus") > 30
       ):
        print("Expected maximum bolus of at least 0 and less than 30")
        return False

    return True


def are_glucose_readings_valid(dates, glucose_values):
    """ Checks that glucose readings are reasonable """
    if any(value < 30 or value > 450 for value in glucose_values):
        print("Expected valid glucose measurement (between 30 and 450 mg/dL)")
        return False

    return True


def are_carb_readings_valid(dates, carb_values, absorption_times):
    """ Checks that carbohydrate inputs are reasonable """
    if any(value < 0 or value > 200 for value in carb_values):
        print("Expected reasonable carbohydrate input" +
              "(between 0 and 200 grams of carbohydrates)")
        return False

    if any(
            absorption < 0 or absorption > 1440
            for absorption in absorption_times):
        print("Expected reasonable carbohydrate absorption time" +
              "(between 0 and 1440 minutes)")
        return False
    return True


def are_insulin_doses_valid(types, start_times, end_times, values):
    """ Checks that dose inputs are reasonable """
    if any(type_.lower() not in
           ["tempbasal", "basal", "basalprofilestart", "bolus",
            "pumpsuspend", "suspend", "resume"] for type_ in types):
        print("There are types in the insulin doses that PyLoop" +
              "does't recognize. The algorithm will still be run, but" +
              "be aware that some doses may not be accounted for.")

    if any(value < 0 or value > 35 for value in values):
        print("Expected reasonable dose values" +
              "(between 0 and 35 U or U/hr)")
        return False

    if any(
            start > end for (start, end) in
            list(
                zip(
                    start_times, end_times
                    )
                )
            ):
        print("Expected dose start times <= ratio end times")
        return False

    return True


def is_insulin_sensitivity_schedule_valid(start_times, end_times, ratios):
    """ Checks that an insulin sensitivity schedule is reasonable """
    if any(value < 10 or value > 400 for value in ratios):
        print("Expected reasonable insulin sensitivity factor" +
              "(between 10 and 400 mg/dL per Unit)")
        return False

    if any(
            start > end for (start, end) in
            list(
                zip(
                    start_times, end_times
                    )
                )[:-1]):  # don't include the last entry because start > end
        print("Expected sensitivity ratio start times <= ratio end times")
        return False

    return True


def are_carb_ratios_valid(dates, ratios):
    """ Checks that carbohydrate ratios are reasonable """
    if any(value < 1 or value > 150 for value in ratios):
        print("Expected reasonable carbohydrate ratios" +
              "(between 1 and 150 grams of carbohydrates per Unit)")
        return False

    return True


def are_basal_rates_valid(start_times, rates, minutes_active):
    """ Checks that carbohydrate ratios are reasonable """
    if any(value < 0 or value > 35 for value in rates):
        print("Expected reasonable basal rates" +
              "(between 0 and 35 Units per hour)")
        return False

    if any(duration > 86400 for duration in minutes_active):
        print("Expected scheduled duration of basal rates to be less than" +
              "a day (86400 minutes)")

    return True


def are_correction_ranges_valid(
        start_times, end_times, minimum_values, maximum_values):
    """ Checks that correction ranges are reasonable """
    if (any(value < 60 or value > 180 for value in minimum_values)
            or any(value < 60 or value > 180 for value in maximum_values)):
        print("Expected reasonable correction ranges" +
              "(somewhere between 60 and 180 mg/dL)")
        return False

    if any(
            start > end for (start, end) in
            list(
                zip(
                    start_times, end_times
                    )
                )[:-1]):
        print("Expected correction range start times <= range end times")
        return False

    return True
