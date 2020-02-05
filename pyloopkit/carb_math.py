#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 13:46:36 2019

@author: annaquinlan
https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/CarbKit/CarbMath.swift
"""
# pylint: disable=R0913, C0200, C0301, R0914, R0915, C0302
import sys
from datetime import timedelta

from pyloopkit.insulin_math import find_ratio_at_time
from pyloopkit.date import (time_interval_since,
                            date_floored_to_time_interval,
                            date_ceiled_to_time_interval)
from pyloopkit import carb_status


def map_(
        carb_entry_starts, carb_entry_quantities, carb_entry_absorptions,
        effect_starts, effect_ends, effect_values,
        carb_ratio_starts, carb_ratios,
        sensitivity_starts, sensitivity_ends, sensitivity_values,
        absorption_time_overrun,
        default_absorption_time,
        delay,
        delta=5
        ):
    """
    Maps a sorted timeline of carb entries to the observed absorbed
    carbohydrates for each, from a timeline of glucose effect velocities.

    This makes some important assumptions:
        - insulin effects, used with glucose to calculate
          counteraction, are "correct"
        - carbs are absorbed completely in the order they were eaten
          without mixing or overlapping effects

    Arguments:
    carb_entry_starts -- list of times of carb entry (datetime objects)
    carb_entry_quantities -- list of grams of carbs eaten
    carb_entry_absorptions -- list of lengths of absorption times (mins)

    effect_starts -- list of start times of carb effect (datetime objects)
    effect_ends -- list of end times of carb effect (datetime objects)
    effect_values -- list of carb effects (mg/dL)

    carb_ratio_starts -- list of start times of carb ratios (time objects)
    carb_ratios -- list of carb ratios (g/U)

    sensitivity_starts -- list of time objects of start times of
                          given insulin sensitivity values
    sensitivity_ends -- list of time objects of start times of
                        given insulin sensitivity values
    sensitivity_values -- list of sensitivities (mg/dL/U)

    absorption_time_overrun -- multiplier to determine absorption time
                               from the specified absorption time
    default_absorption_time -- absorption time to use for unspecified
                               carb entries
    delay -- the time to delay the carb effect
    delta -- time interval between glucose values

    Output:
    3 lists in format (absorption_results, absorption_timelines, carb_entries)
        - lists are matched by index
            - one index represents one carb entry and its corresponding data

        - absorption_results: each index is a list of absorption information
            - structure: [(0) observed grams absorbed,
                          (1) clamped grams,
                          (2) total carbs in entry,
                          (3) remaining carbs,
                          (4) observed absorption start,
                          (5) observed absorption end,
                          (6) estimated time remaining]
        - absorption_timelines: each index is a list that contains
                                lists of timeline values
            - structure: [(0) timeline start time,
                          (1) timeline end time,
                          (2) absorbed value during timeline interval (g)]
            - if a timeline is a list with only "None", less than minimum
              absorption was observed
        - carb_entries: each index is a list of carb entry values
            - these lists are values that were calculated during map_ runtime
            - structure: [(0) carb sensitivities (mg/dL/G of carbohydrate),
                          (1) maximum carb absorption times (min),
                          (2) maximum absorption end times (datetime),
                          (3) last date effects were observed (datetime)
                          (4) total glucose effect expected for entry (mg/dL)]
    """
    assert len(carb_entry_starts) == len(carb_entry_quantities)\
        == len(carb_entry_absorptions), "expected input shapes to match"

    assert len(effect_starts) == len(effect_ends) == len(effect_values), \
        "expected input shapes to match"

    assert len(carb_ratio_starts) == len(carb_ratios),\
        "expected input shapes to match"

    assert len(sensitivity_starts) == len(sensitivity_ends)\
        == len(sensitivity_values), "expected input shapes to match"

    if (not carb_entry_starts
            or not carb_ratios
            or not sensitivity_starts):
        return ([], [], [])

    builder_entry_indexes = list(range(0, len(carb_entry_starts)))

    # CSF is in mg/dL/g
    builder_carb_sensitivities = [
        find_ratio_at_time(
            sensitivity_starts,
            sensitivity_ends,
            sensitivity_values,
            carb_entry_starts[i]
            ) /
        find_ratio_at_time(
            carb_ratio_starts,
            [],
            carb_ratios,
            carb_entry_starts[i]
            )
        for i in builder_entry_indexes
        ]

    # unit: g/s
    builder_max_absorb_times = [
        (carb_entry_absorptions[i]
         or default_absorption_time)
        * absorption_time_overrun
        for i in builder_entry_indexes
        ]

    builder_max_end_dates = [
        carb_entry_starts[i]
        + timedelta(minutes=builder_max_absorb_times[i] + delay)
        for i in builder_entry_indexes
        ]

    last_effect_dates = [
        min(
            builder_max_end_dates[i],
            max(
                effect_ends[len(effect_ends)-1],
                carb_entry_starts[i]
            )
        )
        for i in builder_entry_indexes
        ]

    entry_effects = [
        carb_entry_quantities[i] * builder_carb_sensitivities[i]
        for i in builder_entry_indexes
        ]

    observed_effects = [0 for i in builder_entry_indexes]
    observed_completion_dates = [None for i in builder_entry_indexes]

    observed_timeline_starts = [[] for i in builder_entry_indexes]
    observed_timeline_ends = [[] for i in builder_entry_indexes]
    observed_timeline_carb_values = [[] for i in builder_entry_indexes]

    assert len(builder_entry_indexes) == len(builder_carb_sensitivities)\
        == len(builder_max_absorb_times) == len(builder_max_end_dates)\
        == len(last_effect_dates), "expected shapes to match"

    def add_next_effect(entry_index, effect, start, end):

        if start < carb_entry_starts[entry_index]:
            return

        observed_effects[entry_index] += effect

        if not observed_completion_dates[entry_index]:
            # Continue recording the timeline until
            # 100% of the carbs have been observed
            observed_timeline_starts[entry_index].append(start)
            observed_timeline_ends[entry_index].append(end)
            observed_timeline_carb_values[entry_index].append(
                effect / builder_carb_sensitivities[entry_index]
            )

            # Once 100% of the carbs are observed, track the endDate
            if (
                    observed_effects[entry_index] + sys.float_info.epsilon
                    >= entry_effects[entry_index]
                ):
                observed_completion_dates[entry_index] = end

    for index in range(0, len(effect_starts)):

        if effect_starts[index] >= effect_ends[index]:
            continue

        # Select only the entries whose dates overlap the current date interval
        # These are not always contiguous, as maxEndDate varies between entries
        active_builders = []

        for j in builder_entry_indexes:
            if (effect_starts[index] < builder_max_end_dates[j]
                    and effect_starts[index] >= carb_entry_starts[j]):
                active_builders.append(j)

        # Ignore velocities < 0 when estimating carb absorption.
        # These are most likely the result of insulin absorption increases
        # such as during activity
        effect_value = max(0, effect_values[index]) * delta

        def rate_increase(index_):
            return (carb_entry_quantities[index_]
                    / builder_max_absorb_times[index_]
                    )
        # Sum the minimum absorption rates of each active entry to
        # determine how to split the active effects
        total_rate = 0

        for i in active_builders:
            total_rate += rate_increase(i)

        for b_index in active_builders:
            entry_effect = (carb_entry_quantities[b_index]
                            * builder_carb_sensitivities[b_index]
                           )
            remaining_effect = max(entry_effect - observed_effects[b_index], 0)

            # Apply a portion of the effect to this entry
            partial_effect_value = min(remaining_effect,
                                       (carb_entry_quantities[b_index]
                                        / builder_max_absorb_times[b_index]
                                        ) / total_rate * effect_value
                                       if total_rate != 0 and effect_value != 0
                                       else 0
                                       )

            total_rate -= (carb_entry_quantities[b_index]
                           / builder_max_absorb_times[b_index]
                           )
            effect_value -= partial_effect_value

            add_next_effect(
                b_index,
                partial_effect_value,
                effect_starts[index],
                effect_ends[index]
            )

            # If there's still remainder effects with no additional entries
            # to account them to, count them as overrun on the final entry
            if (effect_value > sys.float_info.epsilon
                    and b_index == (len(active_builders) - 1)
               ):
                add_next_effect(
                    b_index,
                    effect_value,
                    effect_starts[index],
                    effect_ends[index],
                    )

    def absorption_result(builder_index):
        # absorption list structure: [observed grams absorbed, clamped grams,
        # total carbs in entry, remaining carbs, observed absorption start,
        # observed absorption end, estimated time remaining]
        observed_grams = (observed_effects[builder_index]
                          / builder_carb_sensitivities[builder_index])

        entry_grams = carb_entry_quantities[builder_index]

        time = (time_interval_since(
            last_effect_dates[builder_index],
            carb_entry_starts[builder_index]
            ) / 60
                - delay
                )
        min_predicted_grams = linearly_absorbed_carbs(
            entry_grams,
            time,
            builder_max_absorb_times[builder_index]
        )
        clamped_grams = min(
            entry_grams,
            max(min_predicted_grams, observed_grams)
        )

        min_absorption_rate = (carb_entry_quantities[builder_index]
                               / builder_max_absorb_times[builder_index]
                               )
        estimated_time_remaining = ((entry_grams - clamped_grams)
                                    / min_absorption_rate
                                    if min_absorption_rate > 0
                                    else 0)

        absorption = [
            observed_grams,
            clamped_grams,
            entry_grams,
            entry_grams - clamped_grams,
            carb_entry_starts[builder_index],
            observed_completion_dates[builder_index]
            or last_effect_dates[builder_index],
            estimated_time_remaining
        ]

        return absorption

    # The timeline of observed absorption,
    # if greater than the minimum required absorption.
    def clamped_timeline(builder_index):
        entry_grams = carb_entry_quantities[builder_index]

        time = (time_interval_since(
            last_effect_dates[builder_index],
            carb_entry_starts[builder_index]
            ) / 60
                - delay
                )

        min_predicted_grams = linearly_absorbed_carbs(
            entry_grams,
            time,
            builder_max_absorb_times[builder_index]
        )
        observed_grams = (
            observed_effects[builder_index]
            / builder_carb_sensitivities[builder_index]
        )

        output = []
        for i in range(0, len(observed_timeline_starts[builder_index])):
            output.append(
                [
                    observed_timeline_starts[builder_index][i],
                    observed_timeline_ends[builder_index][i],
                    observed_timeline_carb_values[builder_index][i]
                ] if (
                    observed_grams >= min_predicted_grams
                    )
                else [None, None, None])

        return output

    def entry_properties(i):
        return [builder_carb_sensitivities[i],
                builder_max_absorb_times[i],
                builder_max_end_dates[i],
                last_effect_dates[i],
                entry_effects[i]
                ]

    entries = []
    absorptions = []
    timelines = []

    for i in builder_entry_indexes:
        absorptions.append(absorption_result(i))
        timelines.append(clamped_timeline(i))
        entries.append(entry_properties(i))

    assert len(absorptions) == len(timelines) == len(entries),\
        "expect output shapes to match"

    return (absorptions, timelines, entries)


def linearly_absorbed_carbs(total, time, absorption_time):
    """
    Find absorbed carbs using a linear model

    Parameters:
    total -- total grams of carbs
    time -- relative time after eating (in minutes)
    absorption_time --  time for carbs to completely absorb (in minutes)

    Output:
    Grams of absorbed carbs
    """
    return total * linear_percent_absorption_at_time(time, absorption_time)


def linear_unabsorbed_carbs(total, time, absorption_time):
    """
    Find unabsorbed carbs using a linear model

    Parameters:
    total -- total grams of carbs
    time -- relative time after eating (in minutes)
    absorption_time --  time for carbs to completely absorb (in minutes)

    Output:
    Grams of unabsorbed carbs
    """
    return total * (1 - linear_percent_absorption_at_time(time,
                                                          absorption_time
                                                          )
                    )


def linear_percent_absorption_at_time(time, absorption_time):
    """
    Find percent of absorbed carbs using a linear model

    Parameters:
    time -- relative time after eating (in minutes)
    absorption_time --  time for carbs to completely absorb (in minutes)

    Output:
    Percent of absorbed carbs
    """
    if time <= 0:
        return 0
    if time < absorption_time:
        return time / absorption_time
    return 1


def parabolic_absorbed_carbs(total, time, absorption_time):
    """
    Find absorbed carbs using a parabolic model

    Parameters:
    total -- total grams of carbs
    time -- relative time after eating (in minutes)
    absorption_time --  time for carbs to completely absorb (in minutes)

    Output:
    Grams of absorbed carbs
    """
    return total * parabolic_percent_absorption_at_time(time,
                                                        absorption_time
                                                        )


def parabolic_percent_absorption_at_time(time, absorption_time):
    """
    Find percent of absorbed carbs using a parabolic model

    Parameters:
    time -- relative time after eating (in minutes)
    absorption_time --  time for carbs to completely absorb (in minutes)

    Output:
    Percent of absorbed carbs
    """
    if time < 0:
        return 0

    if time <= absorption_time / 2:
        return 2 / pow(absorption_time, 2) * pow(time, 2)

    if time < absorption_time:
        return -1 + 4 / absorption_time * (time - pow(time, 2)
                                           / (2 * absorption_time)
                                           )
    return 1


def simulation_date_range(
        start_times,
        end_times,
        absorption_times,
        default_absorption_time,
        delay,
        delta,
        start=None,
        end=None,
        scaler=1
        ):
    """ Create date range based on carb data and user-specified parameters

    Arguments:
    start_times -- list of datetime object(s) of starts
    end_times -- list of datetime object(s) of ends
    absorption_times -- list of absorption times (in minutes)
    default_absorption_time -- length of interval
    delay -- additional time added to interval
    delta -- what to round to
    start -- specified start date
    end -- specified end date
    scaler -- the factor to extend the absorption time by

    Output:
    tuple with (start_time, end_time) structure
    """
    if not start_times:
        raise ValueError

    if start is not None and end is not None:
        return(date_floored_to_time_interval(start, delta),
               date_ceiled_to_time_interval(end, delta)
               )

    min_date = start_times[0]
    max_date = min_date

    for i in range(0, len(start_times)):
        if start_times[i] < min_date:
            min_date = start_times[i]

        try:
            end_date = end_times[i] + timedelta(
                (absorption_times or default_absorption_time) * scaler
                + delay
            )
        except IndexError:
            end_date = start_times[i] + timedelta(
                minutes=(
                    (absorption_times[i] or default_absorption_time) * scaler
                    + delay)
            )

        if end_date > max_date:
            max_date = end_date

    start_date = date_floored_to_time_interval(start or min_date, delta)
    end_date = date_ceiled_to_time_interval(end or max_date, delta)

    """ 
    Commented out due to a bug in carbs expiring. 
    //todo need to look into why carbs are not expiring. 
    assert start_date <= end_date,\
        "expected start to be less than or equal to end"
    """

    return (start_date, end_date)


def carbs_on_board(
        carb_starts, carb_quantities, carb_absorptions,
        default_absorption_time,
        delay=10,
        delta=5,
        start=None,
        end=None
        ):
    """
    Find the carbs on board non-dynamically

    Arguments:
    carb_starts -- list of times of carb entry (datetime objects)
    carb_quantities -- list of grams of carbs eaten
    carb_absorptions -- list of lengths of absorption times (mins)

    default_absorption_time -- absorption time to use for unspecified
                               carb entries
    delay -- the time to delay the carb effect
    delta -- the differential between timeline entries
    start -- datetime to start calculation of glucose effects
    end -- datetime to stop calculation of glucose effects

    Output:
    Two lists in format (carb on board start dates, carb on board values)
    """
    assert len(carb_starts) == len(carb_quantities)\
        == len(carb_absorptions), "expected input shapes to match"

    if not carb_starts:
        return ([], [])

    (start, end) = simulation_date_range(
        carb_starts,
        [],
        carb_absorptions,
        default_absorption_time,
        delay=delay,
        delta=delta,
        start=start,
        end=end
        )

    date = start
    cob_start_dates = []
    cob_values = []

    def find_partial_effect(i):
        return carbs_on_board_helper(
            carb_starts[i],
            carb_quantities[i],
            date,
            default_absorption_time,
            delay,
            carb_absorptions[i]
            )

    while date <= end:
        cob_sum = 0
        for i in range(0, len(carb_starts)):
            cob_sum += find_partial_effect(i)

        cob_start_dates.append(date)
        cob_values.append(cob_sum)
        date += timedelta(minutes=delta)

    assert len(cob_start_dates) == len(cob_values),\
        "expected output shapes to match"
    return (cob_start_dates, cob_values)


def carbs_on_board_helper(
        carb_start,
        carb_value,
        at_time,
        default_absorption_time,
        delay,
        carb_absorption_time=None
        ):
    """
    Find partial COB for a particular carb entry

    Arguments:
    carb_start -- time of carb entry (datetime objects)
    carb_value -- grams of carbs eaten

    at_date -- date to calculate the glucose effect (datetime object)

    default_absorption_time -- absorption time to use for unspecified
                               carb entries

    delay -- the time to delay the carb effect
    carb_absorption_time -- time carbs will take to absorb (mins)

    Output:
    Carbohydrate value (g)
    """
    time = time_interval_since(at_time, carb_start)
    delay *= 60

    if time >= 0:
        value = (carb_value
                 * (1 - parabolic_percent_absorption_at_time(
                     (time - delay) / 60,
                     carb_absorption_time or default_absorption_time
                     )
                    )
                 )
    else:
        value = 0
    return value


def dynamic_carbs_on_board(
        carb_starts, carb_quantities, carb_absorptions,
        absorptions, timelines,
        default_absorption_time,
        delay=10,
        delta=5,
        start=None,
        end=None,
        scaler=1
        ):
    """
    Find the carbs on board *dynamically*

    Arguments:
    carb_starts -- list of times of carb entry (datetime objects)
    carb_quantities -- list of grams of carbs eaten
    carb_absorptions -- list of lengths of absorption times (mins)

    absorptions -- list of lists of absorption information
                   (computed via map_)
    timelines -- list of lists of carb absorption timelines
                 (computed via map_)

    default_absorption_time -- absorption time to use for unspecified
                               carb entries
    delay -- the time to delay the carb effect
    delta -- the differential between timeline entries
    start -- datetime to start calculation of glucose effects
    end -- datetime to stop calculation of glucose effects
    scaler -- the factor to extend carb absorption by when calculating the
              end time for the COB timeline

    Output:
    Two lists in format (carb on board start dates, carb on board values)
    """
    assert len(carb_starts) == len(carb_quantities)\
        == len(carb_absorptions), "expected input shapes to match"

    assert len(absorptions) == len(timelines),\
        "expected input shapes to match"

    if not carb_starts or not absorptions:
        return ([], [])

    (start, end) = simulation_date_range(
        carb_starts,
        [],
        carb_absorptions,
        default_absorption_time,
        delay=delay,
        delta=delta,
        start=start,
        end=end,
        scaler=scaler
        )

    date = start
    cob_dates = []
    cob_values = []

    def find_partial_cob(i):
        return carb_status.dynamic_carbs_on_board_helper(
            carb_starts[i],
            carb_quantities[i],
            absorptions[i],
            timelines[i],
            date,
            default_absorption_time,
            delay,
            delta,
            carb_absorptions[i]
            )

    while date <= end:
        cob_sum = 0
        for i in range(0, len(carb_starts)):
            cob_sum += find_partial_cob(i)

        cob_dates.append(date)
        cob_values.append(cob_sum)
        date += timedelta(minutes=delta)

    assert len(cob_dates) == len(cob_values),\
        "expected output shapes to match"
    return (cob_dates, cob_values)


def carb_glucose_effects(
        carb_starts, carb_quantities, carb_absorptions,
        carb_ratio_starts, carb_ratios,
        sensitivity_starts, sensitivity_ends, sensitivity_values,
        default_absorption_time,
        delay=10,
        delta=5,
        start=None,
        end=None,
        scaler=1
        ):
    """
    Find the expected effects of carbohydate consumption on blood glucose

    Arguments:
    carb_starts -- list of times of carb entry (datetime objects)
    carb_quantities -- list of grams of carbs eaten
    carb_absorptions -- list of lengths of absorption times (mins)

    carb_ratio_starts -- list of start times of carb ratios (time objects)
    carb_ratios -- list of carb ratios (g/U)

    sensitivity_starts -- list of time objects of start times of
                          given insulin sensitivity values
    sensitivity_ends -- list of time objects of start times of
                        given insulin sensitivity values
    sensitivity_values -- list of sensitivities (mg/dL/U)

    default_absorption_time -- absorption time to use for unspecified
                               carb entries
    delay -- the time to delay the carb effect
    delta -- the differential between timeline entries
    start -- datetime to start calculation of glucose effects
    end -- datetime to stop calculation of glucose effects
    scaler -- the factor to extend carb absorption by when calculating the
              end time for the COB timeline

    Output:
    Two lists in format (effect_start_dates, effect_values)
    """
    assert len(carb_starts) == len(carb_quantities)\
        == len(carb_absorptions), "expected input shapes to match"

    assert len(carb_ratio_starts) == len(carb_ratios),\
        "expected input shapes to match"

    assert len(sensitivity_starts) == len(sensitivity_ends)\
        == len(sensitivity_values), "expected input shapes to match"

    if (not carb_starts
            or not carb_ratio_starts
            or not sensitivity_starts
       ):
        return ([], [])

    (start, end) = simulation_date_range(
        carb_starts,
        [],
        carb_absorptions,
        default_absorption_time,
        delay=delay,
        delta=delta,
        start=start,
        end=end,
        scaler=scaler
        )

    date = start
    effect_start_dates = []
    effect_values = []

    def find_partial_effect(i):
        insulin_sensitivity = find_ratio_at_time(
            sensitivity_starts,
            sensitivity_ends,
            sensitivity_values,
            carb_starts[i]
            )
        carb_ratio = find_ratio_at_time(
            carb_ratio_starts,
            [],
            carb_ratios,
            carb_starts[i]
            )
        return carb_glucose_effect(
            carb_starts[i],
            carb_quantities[i],
            date,
            carb_ratio,
            insulin_sensitivity,
            default_absorption_time,
            delay,
            carb_absorptions[i]
            )

    while date <= end:
        effect_sum = 0
        for i in range(0, len(carb_starts)):
            effect_sum += find_partial_effect(i)

        effect_start_dates.append(date)
        effect_values.append(effect_sum)
        date += timedelta(minutes=delta)

    assert len(effect_start_dates) == len(effect_values),\
        "expected output shapes to match"
    return (effect_start_dates, effect_values)


def carb_glucose_effect(
        carb_start, carb_value,
        at_date,
        carb_ratio,
        insulin_sensitivity,
        default_absorption_time,
        delay,
        carb_absorption_time=None
        ):
    """
    Find partial effect of carbohydate consumption on blood glucose

    Arguments:
    carb_start -- time of carb entry (datetime objects)
    carb_value -- grams of carbs eaten

    at_date -- date to calculate the glucose effect (datetime object)

    carb_ratio -- ratio (g of carbs/U)
    insulin_sensitivity -- sensitivity (mg/dL/U)

    default_absorption_time -- absorption time to use for unspecified
                               carb entries

    delay -- the time to delay the carb effect
    carb_absorption_time -- time carbs will take to absorb (mins)

    Output:
    Glucose effect (mg/dL/min)
    """

    return insulin_sensitivity / carb_ratio * absorbed_carbs(
        carb_start,
        carb_value,
        carb_absorption_time or default_absorption_time,
        at_date,
        delay
        )


def dynamic_glucose_effects(
        carb_starts, carb_quantities, carb_absorptions,
        absorptions, timelines,
        carb_ratio_starts, carb_ratios,
        sensitivity_starts, sensitivity_ends, sensitivity_values,
        default_absorption_time,
        delay=10,
        delta=5,
        start=None,
        end=None,
        scaler=1
        ):
    """
    Find the expected effects of carbohydate consumption on blood glucose
    dynamically

    Arguments:
    carb_starts -- list of times of carb entry (datetime objects)
    carb_quantities -- list of grams of carbs eaten
    carb_absorptions -- list of lengths of absorption times (mins)

    absorptions -- list of lists of absorption information
                   (computed via map_)
    timelines -- list of lists of carb absorption timelines
                 (computed via map_)

    carb_ratio_starts -- list of start times of carb ratios (time objects)
    carb_ratios -- list of carb ratios (g/U)


    sensitivity_starts -- list of time objects of start times of
                          given insulin sensitivity values
    sensitivity_ends -- list of time objects of start times of
                        given insulin sensitivity values
    sensitivity_values -- list of sensitivities (mg/dL/U)

    default_absorption_time -- absorption time to use for unspecified
                               carb entries
    delay -- the time to delay the carb effect
    delta -- the differential between timeline entries
    start -- datetime to start calculation of glucose effects
    end -- datetime to stop calculation of glucose effects
    scaler -- the factor to extend carb absorption by when calculating the
              end time for the COB timeline

    Output:
    Two lists in format (effect_start_dates, effect_values)
    """
    assert len(carb_starts) == len(carb_quantities)\
        == len(carb_absorptions), "expected input shapes to match"

    assert len(carb_ratio_starts) == len(carb_ratios),\
        "expected input shapes to match"

    assert len(sensitivity_starts) == len(sensitivity_ends)\
        == len(sensitivity_values), "expected input shapes to match"

    assert len(absorptions) == len(timelines),\
        "expected input shapes to match"

    if (not carb_starts
            or not carb_ratio_starts
            or not sensitivity_starts
            or not absorptions
       ):
        return ([], [])

    (start, end) = simulation_date_range(
        carb_starts,
        [],
        carb_absorptions,
        default_absorption_time,
        delay=delay,
        delta=delta,
        start=start,
        end=end,
        scaler=scaler
        )

    date = start
    effect_start_dates = []
    effect_values = []

    def find_partial_effect(i):
        insulin_sensitivity = find_ratio_at_time(
            sensitivity_starts,
            sensitivity_ends,
            sensitivity_values,
            carb_starts[i]
            )
        carb_ratio = find_ratio_at_time(
            carb_ratio_starts,
            [],
            carb_ratios,
            carb_starts[i]
            )
        csf = insulin_sensitivity / carb_ratio
        partial_carbs_absorbed = carb_status.dynamic_absorbed_carbs(
            carb_starts[i],
            carb_quantities[i],
            absorptions[i],
            timelines[i],
            date,
            carb_absorptions[i] or default_absorption_time,
            delay,
            delta,
        )

        return csf * partial_carbs_absorbed

    while date <= end:
        effect_sum = 0
        for i in range(0, len(carb_starts)):
            effect_sum += find_partial_effect(i)

        effect_start_dates.append(date)
        effect_values.append(effect_sum)
        date += timedelta(minutes=delta)

    assert len(effect_start_dates) == len(effect_values),\
        "expected output shapes to match"
    return (effect_start_dates, effect_values)


def absorbed_carbs(
        start_date,
        carb_value,
        absorption_time,
        at_date,
        delay
        ):
    """
    Find absorbed carbs using a parabolic model

    Parameters:
    start_date -- date of carb consumption (datetime object)
    carb_value -- carbs consumed
    absorption_time --  time for carbs to completely absorb (in minutes)
    at_date -- date to calculate the absorbed carbs (datetime object)
    delay -- minutes to delay the start of absorption

    Output:
    Grams of absorbed carbs
    """
    time = time_interval_since(at_date, start_date) / 60

    return parabolic_absorbed_carbs(
        carb_value,
        time - delay,
        absorption_time
        )


def filter_date_range_for_carbs(
        starts, values, absorptions,
        start_date,
        end_date
        ):
    """ Returns an array of elements filtered by the specified date range.

    Arguments:
    starts -- start dates (datetime)
    values -- carb values (g)
    absorptions -- absorption times for entries

    start_date -- the earliest date of elements to return
    end_date -- the last date of elements to return

    Output:
    Filtered carb entries in format (starts, values, absorptions)
    """
    # ends might not necesarily be the same length as starts/values
    # because not all types have "end dates"
    assert len(starts) == len(values) == len(absorptions),\
        "expected input shapes to match"

    (filtered_starts,
     filtered_values,
     filtered_absorptions
     ) = ([], [], [])

    for i in range(0, len(starts)):
        if start_date and starts[i] < start_date:
            continue

        if end_date and starts[i] > end_date:
            continue

        filtered_starts.append(starts[i])
        filtered_values.append(values[i])
        filtered_absorptions.append(absorptions[i])

    assert len(filtered_starts) == len(filtered_values)\
        == len(filtered_absorptions), "expected output shapes to match"

    return (
        filtered_starts,
        filtered_values,
        filtered_absorptions
        )
