#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 16:39:23 2019

@author: annaquinlan
"""
# pylint: disable=R0911, W0613
import warnings
from pyloopkit.dose import DoseType


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
        warnings.warn(
            "Error: expected insulin model with DIA between 0"
            + "and 24 hours, peak <= 120 mins, and peak < DIA; stopping run."
        )
        return False

    if (settings.get("momentum_data_interval")
            and settings.get("momentum_data_interval") < 5):
        warnings.warn(
            "Warning: momentum interval is less than 5"
            + " minutes; continuing anyway")

    if (settings.get("suspend_threshold")
            and settings.get("suspend_threshold") < 54
       ):
        warnings.warn(
            "Warning: suspend threshold < 54 mg/dL; continuing anyway"
        )
    elif (settings.get("suspend_threshold")
            and settings.get("suspend_threshold") > 180
       ):
        warnings.warn(
            "Warning: suspend threshold > 180 mg/dL; continuing anyway"
        )

    if any(absorption <= 0 for absorption in settings.get(
                "default_absorption_times")):
        warnings.warn(
            "Error: default absorption times must be positive; stopping run"
        )
        return False

    if (settings.get("max_basal_rate") < 0
            or settings.get("max_basal_rate") > 35
       ):
        warnings.warn(
            "Warning: maximum basal rate is typically at least 0 and less"
            + "than 35 U/hr; continuing anyway"
        )

    if (settings.get("max_bolus") < 0
            or settings.get("max_bolus") > 30
       ):
        warnings.warn(
            "Warning: maximum bolus is typically at least 0 and less than"
            + " 30 U; continuing anyway"
        )

    return True


def are_glucose_readings_valid(dates, glucose_values):
    """ Checks that glucose readings are reasonable """
    if any(value < 0 for value in glucose_values):
        warnings.warn(
            "Error: glucose measurements cannot be negative; stopping run"
        )
        return False

    if any(value < 39 or value > 400 for value in glucose_values):
        warnings.warn(
            "Warning: glucose measurements are typically between 39 and"
            + " 400 mg/dL; continuing anyway"
        )

    return True


def are_carb_readings_valid(dates, carb_values, absorption_times):
    """ Checks that carbohydrate inputs are reasonable """
    if any(value < 0 for value in carb_values):
        warnings.warn(
            "Error: carbohydrate value cannot be negative; stopping run."
        )
        return False

    if any(value > 250 for value in carb_values):
        warnings.warn(
            "Warning: data contains carbohydrate values > 250 g; continuing"
            + " anyway"
        )

    if any(
            absorption < 0 or absorption > 1440
            for absorption in absorption_times):
        warnings.warn(
            "Error: expected carbohydrate absorption times to be between"
            + " 0 & 1440 minutes (0 & 24 hours); stopping run"
        )
        return False

    return True


def are_insulin_doses_valid(types, start_times, end_times, values):
    """ Checks that dose inputs are reasonable """
    if any(type_ not in
           [DoseType.tempbasal, DoseType.basal, DoseType.bolus,
            DoseType.suspend, DoseType.resume, DoseType.meal
            ] for type_ in types):
        warnings.warn(
            "Warning: there are types in the insulin doses that PyLoopKit" +
            " doesn't recognize; continuing anyway"
        )

    if any(value < 0 or value > 35 for value in values):
        warnings.warn(
            "Warning: expected dose values to be between 0 and 35 U or U/hr;"
            + " continuing anyway"
        )

    if any(
            start > end for (start, end) in
            list(
                zip(
                    start_times, end_times
                    )
                )
            ):
        warnings.warn(
            "Error: dose start times cannot be greater than dose end times;"
            + " stopping run")
        return False

    return True


def is_insulin_sensitivity_schedule_valid(start_times, end_times, ratios):
    """ Checks that an insulin sensitivity schedule is reasonable """
    if any(value < 10 or value > 500 for value in ratios):
        warnings.warn(
            "Warning: data contains sensitivity values < 10 or > 500"
            + " mg/dL per Unit; continuing anyway"
            )

    if any(
            start > end for (start, end) in
            list(
                zip(
                    start_times, end_times
                    )
                )[:-1]):  # don't include the last entry because start > end
        warnings.warn(
            "Error: sensitivity ratio start times cannot be greater than ratio"
            + " end times; stopping run."
        )
        return False

    return True


def are_carb_ratios_valid(dates, ratios):
    """ Checks that carbohydrate ratios are reasonable """
    if any(value < 1 or value > 150 for value in ratios):
        warnings.warn(
            "Warning: data contains carb ratios < 1 or > 150 grams of carbs"
            + " per Unit; continuing anyway")

    return True


def are_basal_rates_valid(start_times, rates, minutes_active):
    """ Checks that scheduled basal rates are reasonable """
    if any(value < 0 for value in rates):
        warnings.warn(
            "Error: data contains negative scheduled basal rates; stopping run"
        )
        return False
    elif any(value > 35 for value in rates):
        warnings.warn(
            "Warning: data contains scheduled basal rates > 35 U/hr;"
            + " continuing anyway"
        )

    if any(duration > 1440 for duration in minutes_active):
        warnings.warn(
            "Error: data contains basal rates with scheduled duration greater"
            + " than a day (1440 mins); stopping run"
        )
        return False

    return True


def are_correction_ranges_valid(
        start_times, end_times, minimum_values, maximum_values):
    """ Checks that correction ranges are reasonable """
    if (any(value < 60 or value > 180 for value in minimum_values)
            or any(value < 60 or value > 180 for value in maximum_values)):
        warnings.warn(
            "Warning: correction ranges are typically between 60 and"
            + " 180 mg/dL; continuing anyway")

    if any(
            start > end for (start, end) in
            list(
                zip(
                    start_times, end_times
                    )
                )[:-1]):
        warnings.warn(
            "Error: correction range start times cannot be greater than range"
            + " end times; stopping run"
        )
        return False

    return True
