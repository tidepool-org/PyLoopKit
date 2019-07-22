#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 16:04:15 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/Loop/blob/
8c1dfdba38fbf6588b07cee995a8b28fcf80ef69/Loop/Managers/LoopDataManager.swift
"""
# pylint: disable=R0913, R0914, W0105, C0200
from datetime import timedelta

from carb_store import get_carb_glucose_effects, get_carbs_on_board
from date import time_interval_since
from dose_math import recommended_temp_basal, recommended_bolus
from dose_store import get_glucose_effects
from glucose_store import (get_recent_momentum_effects,
                           get_counteraction_effects)
from insulin_math import find_ratio_at_time
from loop_math import combined_sums, decay_effect, subtracting, predict_glucose


def runner(
        glucose_data,
        insulin_data,
        carb_data,
        settings_dictionary,
        sensitivity_data,
        carb_ratio_data,
        scheduled_basals_data,
        target_range_data,
        last_temp_basal,
        time_to_calculate_at
        ):
    """ Run data through the Loop algorithm and return the predicted glucose
        values, recommended temporary basal, and recommended bolus

    Arguments:
    glucose_data -- tuple in form
        (times of glucose measurements,
         glucose measurements in mg/dL)
    insulin_data -- tuple in form
        (types of dose (tempBasal, bolus, etc),
         start times of insulin delivery,
         end times of insulin delivery,
         amounts of insulin (in U/hr if a basal or U if a bolus),
         scheduled basal rates during the doses (this is *not* mandatory and
            will be added by the runner if it's not present and/or correct)
         )
    carb_data -- tuple in form
        (times of carbohydrate entries,
        amount of carbohydrates eaten,
        absorption times for carbohydrate entries)

    settings_dictionary -- a dictionary containing the needed settings:
        - "model" (the insulin model)
            - if exponential, format is
                [duration of insulin action (in minutes), peak (in minutes)]
                    - child model is typically peaks at 65 mins
                    - adult model is typically peaks at 65 mins
            - if Walsh curve, format is
                [duration of insulin action (in *hours*)]
        - "momentum_time_interval"
            - the interval of glucose data to use for momentum calculation
            - in Loop, default is 15 (minutes)
        - "suspend_threshold"
            - value at which to suspend all insulin delivery (mg/dL)
        - "dynamic_carb_absorption_enabled"
            - whether carb absorption can be calculated dynamically
              (based on deviations in blood glucose levels versus what would
              be expected based on insulin alone)
        - "retrospective_correction_integration_interval"
            - the maximum duration over which to integrate retrospective
              correction changes
            - in Loop, default is 30 (minutes)
        - "recency_interval"
            - the amount of time since a given date that data should be
              considered valid
            - in Loop, default is 15 (minutes)
        - "retrospective_correction_grouping_interval"
            - the interval over which to aggregate changes in glucose for
              retrospective correction
            - in Loop, default is 30 (minutes)
        - "default_absorption_times"
            - the default absorption times to use if unspecified in a
              carbohydrate entry
            - list of default absorption times in minutes in the format
              [slow, medium, fast]
            - in Loop, default is [120 (fast), 180 (medium), 240 (slow)]
        - "max_basal_rate"
            - the maximum basal rate that Loop is allowed to give
        - "max_bolus"
            - the maximum bolus that Loop is allowed to give or recommend

    sensitivity_data -- tuple in form
        (start times for sensitivity ratios,
        end times for sensitivity ratios,
        the sensitivity ratios in mg/dL per U)

    carb_ratio_data -- tuple in form
        (start times for carb ratios,
        carb ratios in grams of carbohydrate per U)

    scheduled_basals_data -- tuple in form
        (start times for basal rates,
        basal rates in U/hour,
         minutes the basal rate is active for)

    target_range_data -- tuple in form
        (start times for the target ranges,
        end times for the target ranges,
        target range minimum values in mg/dL,
        target range maximum values in mg/dL)

    last_temp_basal -- list of information about the last temporary basal
         in the form
         [type of dose,
          start time for the basal,
          end time for the basal,
          value of the basal rate in U/hr]

    time_to_calculate_at -- the "now" time and the time at which to recommend
        the basal rate and bolus

    Output:
        Tuple in format
         ([time of glucose prediction, predicted glucose value in mg/dL],
          recommended basal rate,
          recommended bolus)
    """
    last_glucose_date = glucose_data[0][len(glucose_data[0]) - 1]

    retrospective_start = (
        last_glucose_date
        - timedelta(minutes=settings_dictionary.get(
            "retrospective_correction_integration_interval"))
    )

    earliest_effect_date = time_to_calculate_at - timedelta(hours=24)
    next_effect_date = earliest_effect_date

    (momentum_effect_dates,
     momentum_effect_values
     ) = get_recent_momentum_effects(
         *glucose_data,
         next_effect_date,
         time_to_calculate_at,
         settings_dictionary.get("momentum_time_interval") or 15,
         5
         )

    (insulin_effect_dates,
     insulin_effect_values
     ) = get_glucose_effects(
         *insulin_data,
         next_effect_date,
         *scheduled_basals_data,
         *sensitivity_data,
         settings_dictionary.get("model"),
         )

    if next_effect_date < last_glucose_date and insulin_effect_dates:
        counteraction_effects = get_counteraction_effects(
            *glucose_data,
            next_effect_date,
            insulin_effect_dates, insulin_effect_values
            )

    (carb_effect_dates,
     carb_effect_values
     ) = get_carb_glucose_effects(
         *carb_data,
         retrospective_start,
         *counteraction_effects if
         settings_dictionary.get("dynamic_carb_absorption_enabled")
         else ([], [], []),
         *carb_ratio_data,
         *sensitivity_data,
         settings_dictionary.get("default_absorption_times"),
         end_date=None
         )

    (cob_dates,
     cob_values
     ) = get_carbs_on_board(
         *carb_data,
         time_to_calculate_at,
         *counteraction_effects if
         settings_dictionary.get("dynamic_carb_absorption_enabled")
         else ([], [], []),
         *carb_ratio_data,
         *sensitivity_data,
         settings_dictionary.get("default_absorption_times"),
         end_date=None
         )

    current_cob = cob_values[
        closest_prior_to_date(
            time_to_calculate_at,
            cob_dates
            )
        ]

    retrospective_glucose_effects = update_retrospective_glucose_effect(
        *glucose_data,
        carb_effect_dates, carb_effect_values,
        *counteraction_effects,
        settings_dictionary.get("recency_interval"),
        settings_dictionary.get("retrospective_correction_grouping_interval"),
        time_to_calculate_at
        )

    recommendations = update_predicted_glucose_and_recommended_basal_and_bolus(
        time_to_calculate_at,
        *glucose_data,
        momentum_effect_dates, momentum_effect_values,
        carb_effect_dates, carb_effect_values,
        insulin_effect_dates, insulin_effect_values,
        *retrospective_glucose_effects,
        *target_range_data,
        settings_dictionary.get("suspend_threshold"),
        *sensitivity_data,
        settings_dictionary.get("model"),
        *scheduled_basals_data,
        settings_dictionary.get("max_basal_rate"),
        settings_dictionary.get("max_bolus"),
        last_temp_basal
        )

    return recommendations


def closest_prior_to_date(date_to_compare, dates):
    """ Returns the index of the closest element in the sorted sequence
        prior to the specified date
    """
    for date in dates:
        if date <= date_to_compare:
            closest_element = date
        else:
            break

    return dates.index(closest_element)


def update_retrospective_glucose_effect(
        glucose_dates, glucose_values,
        carb_effect_dates, carb_effect_values,
        counteraction_starts, counteraction_ends, counteraction_values,
        recency_interval,
        retrospective_correction_grouping_interval,
        now_time,
        effect_duration=60,
        delta=5
        ):
    """
    Generate an effect based on how large the discrepancy is between the
    current glucose and its predicted value.

    Arguments:
    glucose_dates -- time of glucose value (datetime)
    glucose_values -- value at the time of glucose_date

    carb_effect_dates -- date the carb effects occur at (datetime)
    carb_effect_values -- value of carb effect

    counteraction_starts -- start times for counteraction effects
    counteraction_ends -- end times for counteraction effects
    counteraction_values -- values of counteraction effects

    recency_interval -- amount of time since a given date that data should be
                        considered valid
    retrospective_correction_grouping_interval -- interval over which to
        aggregate changes in glucose for retrospective correction

    now_time -- the time the loop is being run at
    effect_duration -- the length of time to calculate the retrospective
                       glucose effect out to
    delta -- time interval between glucose values (mins)

    Output:
    Retrospective glucose effect information
    """
    assert len(glucose_dates) == len(glucose_values),\
        "expected input shapes to match"

    assert len(carb_effect_dates) == len(carb_effect_values),\
        "expected input shapes to match"

    assert len(counteraction_starts) == len(counteraction_ends)\
        == len(counteraction_values), "expected input shapes to match"

    if not carb_effect_dates or not glucose_dates:
        return ([], [])

    (discrepancy_starts, discrepancy_values) = subtracting(
        counteraction_starts, counteraction_ends, counteraction_values,
        carb_effect_dates, [], carb_effect_values,
        delta
        )

    retrospective_glucose_discrepancies_summed = combined_sums(
        discrepancy_starts, discrepancy_starts, discrepancy_values,
        retrospective_correction_grouping_interval * 1.01
        )

    # Our last change should be recent, otherwise clear the effects
    if (time_interval_since(
            retrospective_glucose_discrepancies_summed[1][-1],
            now_time) / 60
            > recency_interval
       ):
        return ([], [])

    discrepancy_time = max(
        0,
        retrospective_correction_grouping_interval
        )

    velocity = (
        retrospective_glucose_discrepancies_summed[2][-1]
        / discrepancy_time
        )

    return decay_effect(
        glucose_dates[-1], glucose_values[-1],
        velocity,
        effect_duration
        )
