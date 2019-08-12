#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 16:04:15 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/Loop/blob/
8c1dfdba38fbf6588b07cee995a8b28fcf80ef69/Loop/Managers/LoopDataManager.swift
"""
# pylint: disable=R0913, R0914, W0105, C0200, R0916
from datetime import timedelta

from carb_store import get_carb_glucose_effects, get_carbs_on_board
from date import time_interval_since
from dose_math import recommended_temp_basal, recommended_bolus
from dose_store import get_glucose_effects
from glucose_store import (get_recent_momentum_effects,
                           get_counteraction_effects)
from input_validation_tools import (
    are_settings_valid, are_glucose_readings_valid, are_carb_readings_valid,
    is_insulin_sensitivity_schedule_valid, are_carb_ratios_valid,
    are_basal_rates_valid, are_correction_ranges_valid,
    are_insulin_doses_valid)
from insulin_math import find_ratio_at_time
from loop_math import (combined_sums, decay_effect, subtracting,
                       predict_glucose)


def update(
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
         amounts of insulin (in U/hr if a basal or U if a bolus)
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
    # check that the inputs make sense before doing math with them
    if (
            not are_settings_valid(settings_dictionary)
            or not are_glucose_readings_valid(*glucose_data)
            or not are_carb_readings_valid(*carb_data)
            or not is_insulin_sensitivity_schedule_valid(*sensitivity_data)
            or not are_carb_ratios_valid(*carb_ratio_data)
            or not are_basal_rates_valid(*scheduled_basals_data)
            or not are_correction_ranges_valid(*target_range_data)
            or not are_insulin_doses_valid(*insulin_data)):
        return []

    last_glucose_date = glucose_data[0][len(glucose_data[0]) - 1]

    retrospective_start = (
        last_glucose_date
        - timedelta(minutes=settings_dictionary.get(
            "retrospective_correction_integration_interval"))
    )

    # calculate a maximum of 24 hours of effects
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

    # calculate previous insulin effects in order to later calculate the
    # insulin counteraction effects
    (insulin_effect_dates,
     insulin_effect_values
     ) = get_glucose_effects(
         *insulin_data,
         next_effect_date,
         *scheduled_basals_data,
         *sensitivity_data,
         settings_dictionary.get("model"),
         delay=settings_dictionary.get("insulin_delay") or 10
         )

    # calculate future insulin effects for the purposes of predicting glucose
    now_to_dia_insulin_effects = get_glucose_effects(
        *insulin_data,
        time_to_calculate_at,
        *scheduled_basals_data,
        *sensitivity_data,
        settings_dictionary.get("model"),
        delay=settings_dictionary.get("insulin_delay") or 10
        )

    # if our BG data is current and we know the expected insulin effects,
    # calculate tbe counteraction effects
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
         delay=settings_dictionary.get("carb_delay") or 10
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
         delay=settings_dictionary.get("carb_delay") or 10
         )

    current_cob = cob_values[
        closest_prior_to_date(
            time_to_calculate_at,
            cob_dates
            )
        ] if cob_dates else 0

    if settings_dictionary.get("retrospective_correction_enabled"):
        retrospective_glucose_effects = update_retrospective_glucose_effect(
            *glucose_data,
            carb_effect_dates, carb_effect_values,
            *counteraction_effects,
            settings_dictionary.get("recency_interval"),
            settings_dictionary.get(
                "retrospective_correction_grouping_interval"
            ),
            time_to_calculate_at
            )
    else:
        retrospective_glucose_effects = ([], [])

    recommendations = update_predicted_glucose_and_recommended_basal_and_bolus(
        time_to_calculate_at,
        *glucose_data,
        momentum_effect_dates, momentum_effect_values,
        carb_effect_dates, carb_effect_values,
        *now_to_dia_insulin_effects,
        *retrospective_glucose_effects,
        *target_range_data,
        settings_dictionary.get("suspend_threshold"),
        *sensitivity_data,
        settings_dictionary.get("model"),
        *scheduled_basals_data,
        settings_dictionary.get("max_basal_rate"),
        settings_dictionary.get("max_bolus"),
        last_temp_basal,
        rate_rounder=settings_dictionary.get("rate_rounder")
        )

    recommendations["insulin_effect_dates"] = now_to_dia_insulin_effects[0]
    recommendations["insulin_effect_values"] = now_to_dia_insulin_effects[1]

    recommendations["counteraction_effect_dates"] = counteraction_effects[0]
    recommendations["counteraction_effect_values"] = counteraction_effects[1]

    recommendations["momentum_effect_dates"] = momentum_effect_dates
    recommendations["momentum_effect_values"] = momentum_effect_values

    recommendations["carb_effect_dates"] = carb_effect_dates
    recommendations["carb_effect_values"] = carb_effect_values

    recommendations["retrospective_effect_dates"] = (
        retrospective_glucose_effects[0] or None
    )
    recommendations["retrospective_effect_values"] = (
        retrospective_glucose_effects[1] or None
    )
    recommendations["carbs_on_board"] = current_cob
    recommendations["cob_timeline_dates"] = cob_dates
    recommendations["cob_timeline_values"] = cob_values

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
    Retrospective glucose effect information in format
    (retrospective_effect_dates, retrospective_effect_values)
    """
    assert len(glucose_dates) == len(glucose_values),\
        "expected input shapes to match"

    assert len(carb_effect_dates) == len(carb_effect_values),\
        "expected input shapes to match"

    assert len(counteraction_starts) == len(counteraction_ends)\
        == len(counteraction_values), "expected input shapes to match"

    if not glucose_dates or not carb_effect_dates or not counteraction_starts:
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
            now_time,
            retrospective_glucose_discrepancies_summed[1][-1])
            > recency_interval * 60
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


def get_pending_insulin(
        at_date,
        basal_starts, basal_rates, basal_minutes,
        last_temp_basal,
        pending_bolus_amount=None
    ):
    """ Get the pending insulin for the purposes of calculating a recommended
        bolus

    Arguments:
    at_date -- the "now" time (roughly equivalent to datetime.now)

    basal_starts -- list of times the basal rates start at
    basal_rates -- list of basal rates (U/hr)
    basal_minutes -- list of basal lengths (in mins)

    last_temp_basal -- information about the last temporary basal in the form
                       [type, start time, end time, basal rate]
    pending_bolus_amount -- amount of unconfirmed bolus insulin (U)

    Output:
    Amount of insulin that is "pending"
    """
    assert len(basal_starts) == len(basal_rates),\
        "expected input shapes to match"

    if (not basal_starts
            or not last_temp_basal
            or last_temp_basal[1] > last_temp_basal[2]
       ):
        return 0

    # if the end date for the temp basal is greater than current date,
    # find the pending insulin
    if (last_temp_basal[2] > at_date
            and last_temp_basal[0].lower() in ["tempbasal", "basal"]):
        normal_basal_rate = find_ratio_at_time(
            basal_starts, [], basal_rates, at_date
        )
        remaining_time = time_interval_since(
            last_temp_basal[2],
            at_date
        ) / 60 / 60

        remaining_units = (
            last_temp_basal[3] - normal_basal_rate
        ) * remaining_time
        pending_basal_insulin = max(0, remaining_units)

    else:
        pending_basal_insulin = 0

    if pending_bolus_amount:
        pending_bolus = pending_bolus_amount
    else:
        pending_bolus = 0

    return pending_basal_insulin + pending_bolus


def update_predicted_glucose_and_recommended_basal_and_bolus(
        at_date,
        glucose_dates, glucose_values,
        momentum_dates, momentum_values,
        carb_effect_dates, carb_effect_values,
        insulin_effect_dates, insulin_effect_values,
        retrospective_effect_dates, retrospective_effect_values,
        target_starts, target_ends, target_mins, target_maxes,
        suspend_threshold,
        sensitivity_starts, sensitivity_ends, sensitivity_values,
        model,
        basal_starts, basal_rates, basal_minutes,
        max_basal_rate, max_bolus,
        last_temp_basal,
        duration=30,
        continuation_interval=11,
        rate_rounder=None
        ):
    """ Generate glucose predictions, then use the predicted glucose along
        with settings and dose data to recommend a temporary basal rate and
        a bolus

    Arguments:
    at_date -- date to calculate the temp basal and bolus recommendations

    glucose_dates -- dates of glucose values (datetime)
    glucose_values -- glucose values (in mg/dL)

    momentum_dates -- times of calculated momentums (datetime)
    momentum_values -- values (mg/dL) of momentums

    carb_effect_dates -- times of carb effects (datetime)
    carb_effect -- values (mg/dL) of effects from carbs

    insulin_effect_dates -- times of insulin effects (datetime)
    insulin_effect -- values (mg/dL) of effects from insulin

    correction_effect_dates -- times of retrospective effects (datetime)
    correction_effect -- values (mg/dL) retrospective glucose effects

    target_starts -- start times for given target ranges (datetime)
    target_ends -- stop times for given target ranges (datetime)
    target_mins -- the lower bounds of target ranges (mg/dL)
    target_maxes -- the upper bounds of target ranges (mg/dL)

    suspend_threshold -- value at which to suspend all insulin delivery (mg/dL)

    sensitivity_starts -- list of time objects of start times of
                          given insulin sensitivity values
    sensitivity_ends -- list of time objects of start times of
                        given insulin sensitivity values
    sensitivity_values -- list of sensitivities (mg/dL/U)

    model -- list of insulin model parameters in format [DIA, peak_time] if
             exponential model, or [DIA] if Walsh model

    basal_starts -- list of times the basal rates start at
    basal_rates -- list of basal rates(U/hr)
    basal_minutes -- list of basal lengths (in mins)

    max_basal_rate -- max basal rate that Loop can give (U/hr)
    max_bolus -- max bolus that Loop can give (U)

    last_temp_basal -- list of last temporary basal information in format
                       [type, start time, end time, basal rate]
    duration -- length of the temp basal (mins)
    continuation_interval -- length of time before an ongoing temp basal
                             should be continued with a new command (mins)
    rate_rounder -- the smallest fraction of a unit supported in basal
                    delivery; if None, no rounding is performed

    Output:
    The predicted glucose values, recommended temporary basal, and
    recommended bolus in the format [
        (predicted glucose times, predicted glucose values),
        temporary basal recommendation,
        bolus recommendation
    ]
    """
    assert glucose_dates, "expected to receive glucose data"

    assert target_starts and sensitivity_starts and basal_starts and model,\
        "expected to receive complete settings data"

    if (not momentum_dates
            and not carb_effect_dates
            and not insulin_effect_dates
       ):
        print("Expected to receive effect data")
        return (None, None, None)

    predicted_glucoses = predict_glucose(
        glucose_dates[-1], glucose_values[-1],
        momentum_dates, momentum_values,
        carb_effect_dates, carb_effect_values,
        insulin_effect_dates, insulin_effect_values,
        retrospective_effect_dates, retrospective_effect_values
        )

    # Dosing requires prediction entries at least as long as the insulin
    # model duration. If our prediction is shorter than that, extend it here.
    if len(model) == 1:  # Walsh model
        final_date = glucose_dates[-1] + timedelta(hours=model[0])
    else:
        final_date = glucose_dates[-1] + timedelta(minutes=model[0])

    if predicted_glucoses[0][-1] < final_date:
        predicted_glucoses[0].append(final_date)
        predicted_glucoses[1].append(predicted_glucoses[1][-1])

    pending_insulin = get_pending_insulin(
        at_date,
        basal_starts, basal_rates, basal_minutes,
        last_temp_basal
    )

    temp_basal = recommended_temp_basal(
        *predicted_glucoses,
        target_starts, target_ends, target_mins, target_maxes,
        at_date,
        suspend_threshold,
        sensitivity_starts, sensitivity_ends, sensitivity_values,
        model,
        basal_starts, basal_rates, basal_minutes,
        max_basal_rate,
        last_temp_basal,
        duration,
        continuation_interval,
        rate_rounder
        )

    bolus = recommended_bolus(
        *predicted_glucoses,
        target_starts, target_ends, target_mins, target_maxes,
        at_date,
        suspend_threshold,
        sensitivity_starts, sensitivity_ends, sensitivity_values,
        model,
        pending_insulin,
        max_bolus,
        rate_rounder
        )

    return {
        "predicted_glucose_dates": predicted_glucoses[0],
        "predicted_glucose_values": predicted_glucoses[1],
        "recommended_temp_basal": temp_basal,
        "recommended_bolus": bolus
    }
