#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 10:29:59 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/InsulinKit/InsulinMath.swift
"""
# pylint: disable=R0913, R0914, R0912, C0200, R0915, R1702, C0302, R0911
from math import floor
from datetime import timedelta, datetime
import sys

from pyloopkit.date import time_interval_since, time_interval_since_reference_date
from pyloopkit.dose import DoseType
from pyloopkit.loop_math import simulation_date_range_for_samples
from pyloopkit.dose_entry import net_basal_units, total_units_given
from pyloopkit.exponential_insulin_model import percent_effect_remaining
from pyloopkit.walsh_insulin_model import walsh_percent_effect_remaining

MAXIMUM_RESERVOIR_DROP_PER_MINUTE = 6.5
DISTANT_PAST = datetime.fromisoformat("2001-01-01T00:00:00")
TIMEZONE_DISTANT_PAST = datetime.strptime(
    "2001-01-01 00:00:00 +0000",
    "%Y-%m-%d %H:%M:%S %z"
    )
DISTANT_FUTURE = datetime.fromisoformat("2050-01-01T00:00:00")
TIMEZONE_DISTANT_FUTURE = datetime.strptime(
    "2050-01-01 00:00:00 +0000",
    "%Y-%m-%d %H:%M:%S %z"
    )


def total_delivery(dose_types, starts, ends, values):
    """ Calculates the total insulin delivery for a collection of doses

    Arguments:
    dose_types -- types of doses (basal, bolus, etc)
    starts -- datetime objects of times doses started at
    ends -- datetime objects of times doses ended at
    values -- amount, in U/hr (if a basal) or U (if bolus) of insulin in dose

    Output:
    The total insulin insulin, in Units
    """
    assert len(dose_types) == len(starts) == len(ends) == len(values),\
        "expected input shapes to match"

    total = 0
    for i in range(0, len(dose_types)):
        total += total_units_given(
            dose_types[i],
            values[i],
            starts[i],
            ends[i]
        )

    if total < 0:
        return 0

    return total


def dose_entries(reservoir_dates, unit_volumes):
    """ Converts a continuous, chronological sequence of reservoir values
        to a sequence of doses
    Runtime: O(n)

    Arguments:
    reservoir_dates -- list of datetime objects
    unit_volumes -- list of reservoir volumes (in units of insulin)

    Output:
    A tuple of lists in (dose_type (basal/bolus), start_dates, end_dates,
        insulin_values) format
    """
    assert len(reservoir_dates) > 1,\
        "expected input lists to contain two or more items"
    assert len(reservoir_dates) == len(unit_volumes),\
        "expected input shape to match"

    dose_types = []
    start_dates = []
    end_dates = []
    insulin_values = []

    previous_date = reservoir_dates[0]
    previous_unit_volume = unit_volumes[0]

    for i in range(1, len(reservoir_dates)):
        volume_drop = previous_unit_volume - unit_volumes[i]
        duration = time_interval_since(
            reservoir_dates[i],
            previous_date
        )

        if (duration > 0 and 0 <= volume_drop <=
                MAXIMUM_RESERVOIR_DROP_PER_MINUTE * duration / 60):
            dose_types.append(DoseType.tempbasal)
            start_dates.append(previous_date)
            end_dates.append(reservoir_dates[i])
            insulin_values.append(volume_drop)

        previous_date = reservoir_dates[i]
        previous_unit_volume = unit_volumes[i]

    assert len(dose_types) == len(start_dates) == len(end_dates) ==\
        len(insulin_values), "expected output shape to match"

    return (dose_types, start_dates, end_dates, insulin_values)


def is_continuous(reservoir_dates, unit_volumes, start, end,
                  maximum_duration):
    """ Whether a span of chronological reservoir values is considered
        continuous and therefore reliable.

    Reservoir values of 0 are automatically considered unreliable due to
    the assumption that an unknown amount of insulin can be delivered after
    the 0 marker.

    Arguments:
    reservoir_dates -- list of datetime objects that correspond by index to
                        unit_volumes
    unit_volumes -- volume of reservoir in units, corresponds by index to
                    reservoir_dates
    start -- datetime object that is start of the interval which to validate
             continuity
    end -- datetime object that is end of the interval which to validate
             continuity
    maximum_duration -- the maximum interval to consider reliable for a
                        reservoir-derived dose

    Variable names:
    start_date -- the beginning of the interval in which to validate
                   continuity
    end_date -- the end of the interval in which to validate continuity

    Outputs:
    Whether the reservoir values meet the critera for continuity
    """
    try:
        first_date_value = reservoir_dates[0]
        first_volume_value = unit_volumes[0]
    except IndexError:
        return False

    if end < start:
        return False

    start_date = start
    # The first value has to be at least as old as the start date
    # as a reference point.
    if first_date_value > start_date:
        return False

    last_date_value = first_date_value
    last_volume_value = first_volume_value

    for i in range(0, len(unit_volumes)):  # pylint: disable=C0200
        # Volume and interval validation only applies for values in
        # the specified range
        if reservoir_dates[i] < start_date or reservoir_dates[i] > end:
            last_date_value = reservoir_dates[i]
            last_volume_value = unit_volumes[i]
            continue
        # We can't trust 0. What else was delivered?
        if unit_volumes[i] <= 0:
            return False
        # Rises in reservoir volume indicate a rewind + prime, and primes
        # can be easily confused with boluses.
        # Small rises (1 U) can be ignored as they're indicative of a
        # mixed-precision sequence.
        if unit_volumes[i] > last_volume_value + 1:
            return False
        # Ensure no more than the maximum interval has passed
        if (time_interval_since(reservoir_dates[i], last_date_value)
                > maximum_duration * 60):
            return False

        last_date_value = reservoir_dates[i]
        last_volume_value = unit_volumes[i]

    return True


def reconciled(dose_types, start_dates, end_dates, values, delivered_units):
    """ Maps a timeline of dose entries with overlapping start and end dates
        to a timeline of doses that represents actual insulin delivery.

    Arguments:
    dose_types -- list of types of doses (basal, bolus, etc)
    start_dates -- list of datetime objects representing the dates
                   the doses started at
    end_dates -- list of datetime objects representing the dates
                   the doses ended at
    values -- list of insulin values for doses
    scheduled_basal_rates -- basal rates scheduled during the times of doses

    Output:
    Tuple with *four* of the dose properties (does not include scheduled basal
    rates), reconciled as TempBasal and Bolus records; these lists are
    *not* always in order of time
    """
    # this function does not return a list of scheduled basal rates
    output_types = []
    output_starts = []
    output_ends = []
    output_values = []
    output_delivered_units = []

    last_suspend_index = None
    last_basal = []

    assert len(dose_types) == len(start_dates) == len(end_dates) ==\
        len(values) == len(delivered_units),\
        "expected input shapes to match"

    for (i, type_) in enumerate(dose_types):
        if type_ == DoseType.bolus:
            output_types.append(type_)
            output_starts.append(start_dates[i])
            output_ends.append(end_dates[i])
            output_values.append(values[i])
            output_delivered_units.append(delivered_units[i])

        elif type_ in [DoseType.tempbasal, DoseType.basal]:
            if last_basal and not last_suspend_index:
                last = last_basal
                end_date = min(last[2], start_dates[i])

                # ignore zero-duration doses
                if end_date > last[1]:
                    output_types.append(last[0])
                    output_starts.append(last[1])
                    output_ends.append(end_date)
                    output_values.append(last[3])
                    output_delivered_units.append(last[4])
            last_basal = [type_, start_dates[i], end_dates[i],
                          values[i], delivered_units[i]]

        elif type_ == DoseType.resume:
            if last_suspend_index:
                suspend = last_suspend_index

                output_types.append(dose_types[suspend])
                output_starts.append(start_dates[suspend])
                output_ends.append(end_dates[i])
                output_values.append(values[suspend])
                output_delivered_units.append(delivered_units[suspend])

                last_suspend_index = None

                # Continue temp basals that may have started before suspending
                if last_basal:
                    last = last_basal
                    if last[2] > end_dates[i]:
                        last_basal = [last[0], end_dates[i], last[2], last[3], last[4]]
                    else:
                        last_basal = []

        elif type_ == DoseType.suspend:
            if last_basal:
                last = last_basal

                output_types.append(last[0])
                output_starts.append(last[1])
                output_ends.append(min(last[2], start_dates[i]))
                output_values.append(last[3])
                output_delivered_units.append(last[4])

                if last[2] <= start_dates[i]:
                    last_basal = []

            # add the suspend immediately if it's already been normalized
            # before being passed into reconciled()
            if start_dates[i] == end_dates[i]:
                last_suspend_index = i
            else:
                output_types.append(type_)
                output_starts.append(start_dates[i])
                output_ends.append(end_dates[i])
                output_values.append(values[i])
                output_delivered_units.append(delivered_units[i])

        elif type_ == DoseType.meal:
            output_types.append(type_)
            output_starts.append(start_dates[i])
            output_ends.append(end_dates[i])
            output_values.append(values[i])
            output_delivered_units.append(delivered_units[i])

    if last_suspend_index is not None:
        output_types.append(dose_types[last_suspend_index])
        output_starts.append(start_dates[last_suspend_index])
        output_ends.append(end_dates[last_suspend_index])
        output_values.append(values[last_suspend_index])
        output_delivered_units.append(delivered_units[last_suspend_index])

    elif (last_basal
          and last_basal[2] > last_basal[1]
          ):
        # I slightly modified this because it wasn't dealing with the last
        # basal correctly
        output_types.append(last_basal[0])
        output_starts.append(last_basal[1])
        output_ends.append(last_basal[2])
        output_values.append(last_basal[3])
        output_delivered_units.append(last_basal[4])

    assert len(output_types) == len(output_starts) == len(output_ends) ==\
        len(output_values) == len(output_delivered_units), "expected output shape to match"

    return (output_types,
            output_starts,
            output_ends,
            output_values,
            output_delivered_units
            )


def annotated(
        dose_types, start_dates, end_dates, values, delivered_units,
        basal_start_times, basal_rates, basal_minutes,
        convert_to_units_hr=True
    ):
    """ Annotates doses with the context of the scheduled basal rates

    Arguments:
    dose_types -- list of types of dose (basal, bolus, etc)
    dose_start_dates -- start dates of the doses (datetime obj)
    dose_end_dates -- end dates of the doses (datetime obj)
    values -- actual basal rates of doses in U/hr (if a basal)
             or the value of the boluses in U

    basal_start_times -- list of times the basal rates start at
    basal_rates -- list of basal rates(U/hr)
    basal_minutes -- list of basal lengths (in mins)

    convert_to_units_hr -- set to True if you want to convert the doses to U/hr
        (ex: 0.05 U given from 1/1/01 1:00:00 to 1/1/01 1:05:00 -> 0.6 U/hr);
        this will normally be for reservoir values

    Output:
    6 lists of annotated dose properties
    """
    assert len(dose_types) == len(start_dates) == len(end_dates) ==\
        len(values) == len(delivered_units),\
        "expected input shapes to match"

    assert len(basal_start_times) == len(basal_rates) == len(basal_minutes),\
        "expected input shapes to match"

    if not dose_types or not basal_start_times:
        return ([], [], [], [], [], [])

    output_types = []
    output_start_dates = []
    output_end_dates = []
    output_values = []
    output_scheduled_basal_rates = []
    output_delivered_units = []

    for i in range(0, len(dose_types)):
        (dose_type,
         start_date,
         end_date,
         value,
         scheduled_basal_rate,
         delivered_unit
         ) = annotate_individual_dose(
             dose_types[i], start_dates[i], end_dates[i], values[i], delivered_units[i],
             basal_start_times, basal_rates, basal_minutes,
             convert_to_units_hr
             )

        output_types.extend(dose_type)
        output_start_dates.extend(start_date)
        output_end_dates.extend(end_date)
        output_values.extend(value)
        output_scheduled_basal_rates.extend(scheduled_basal_rate)
        output_delivered_units.extend(delivered_unit)

    assert len(output_types) == len(output_start_dates) ==\
        len(output_end_dates) == len(output_values) ==\
        len(output_scheduled_basal_rates) == len(output_delivered_units), "expected output shapes to match"

    return (output_types,
            output_start_dates,
            output_end_dates,
            output_values,
            output_scheduled_basal_rates,
            output_delivered_units
            )


def annotate_individual_dose(dose_type, dose_start_date, dose_end_date, value, delivered_unit,
                             basal_start_times, basal_rates, basal_minutes,
                             convert_to_units_hr=True):
    """ Annotates a dose with the context of the scheduled basal rate
        If the dose crosses a schedule boundary, it will be split into
        multiple doses so each dose has a single scheduled basal rate.

    Arguments:
    dose_type -- type of dose (basal, bolus, etc)
    dose_start_date -- start date of the dose (datetime obj)
    dose_end_date -- end date of the dose (datetime obj)
    value -- actual basal rate of dose in U/hr (if a basal)
             or the value of the bolus in U
    basal_start_times -- list of times the basal rates start at
    basal_rates -- list of basal rates(U/hr)
    basal_minutes -- list of basal lengths (in mins)
    convert_to_units_hr -- set to True if you want to convert a dose to U/hr
        (ex: 0.05 U given from 1/1/01 1:00:00 to 1/1/01 1:05:00 -> 0.6 U/hr)

    Output:
    Tuple with properties of doses, annotated with the current basal rates
    """
    if dose_type not in [DoseType.basal, DoseType.tempbasal,
                                 DoseType.suspend]:
        return ([dose_type], [dose_start_date], [dose_end_date], [value],
                [0], [delivered_unit])

    output_types = []
    output_start_dates = []
    output_end_dates = []
    output_values = []
    output_scheduled_basal_rates = []
    output_delivered_units = []

    # these are the lists containing the scheduled basal value(s) within
    # the temp basal's duration
    (sched_basal_starts,
     sched_basal_ends,
     sched_basal_rates
     ) = between(
         basal_start_times,
         basal_rates,
         basal_minutes,
         dose_start_date,
         dose_end_date,
         )

    for i in range(0, len(sched_basal_starts)):
        if i == 0:
            start_date = dose_start_date
        else:
            start_date = sched_basal_starts[i]

        if i == len(sched_basal_starts) - 1:
            end_date = dose_end_date
        else:
            end_date = sched_basal_starts[i+1]

        output_types.append(dose_type)
        output_start_dates.append(start_date)
        output_end_dates.append(end_date)

        if convert_to_units_hr:
            output_values.append(
                0 if dose_type == DoseType.suspend else value
                / (time_interval_since(dose_end_date, dose_start_date)/60/60))
        else:
            output_values.append(value)

        output_scheduled_basal_rates.append(sched_basal_rates[i])
        output_delivered_units.append(delivered_unit)

    assert len(output_types) == len(output_start_dates) ==\
        len(output_end_dates) == len(output_values) ==\
        len(output_scheduled_basal_rates) == len(output_delivered_units), "expected output shapes to match"

    return (output_types,
            output_start_dates,
            output_end_dates,
            output_values,
            output_scheduled_basal_rates,
            output_delivered_units
            )


def between(
        basal_start_times, basal_rates, basal_minutes,
        start_date, end_date,
        repeat_interval=24
    ):
    """ Returns a slice of scheduled basal rates that occur between two dates

    Arguments:
    basal_start_times -- list of times the basal rates start at
    basal_rates -- list of basal rates(U/hr)
    basal_minutes -- list of basal lengths (in mins)
    start_date -- start date of the range (datetime obj)
    end_date -- end date of the range (datetime obj)
    repeat_interval -- the duration over which the rates repeat themselves
                       (24 hours by default)

    Output:
    Tuple in format (basal_start_times, basal_rates, basal_minutes) within
    the range of dose_start_date and dose_end_date
    """
    timezone_info = start_date.tzinfo
    if start_date > end_date:
        return ([], [], [])

    reference_time_interval = timedelta(
        hours=basal_start_times[0].hour,
        minutes=basal_start_times[0].minute,
        seconds=basal_start_times[0].second
    )
    max_time_interval = (
        reference_time_interval
        + timedelta(hours=repeat_interval)
    )

    start_offset = schedule_offset(start_date, basal_start_times[0])

    end_offset = (
        start_offset
        + timedelta(seconds=time_interval_since(end_date, start_date))
    )

    # if a dose is crosses days, split it into separate doses
    if end_offset > max_time_interval:
        boundary_date = start_date + (max_time_interval - start_offset)
        (start_times_1,
         end_times_1,
         basal_rates_1
         ) = between(
             basal_start_times,
             basal_rates,
             basal_minutes,
             start_date,
             boundary_date,
             repeat_interval=repeat_interval
             )
        (start_times_2,
         end_times_2,
         basal_rates_2
         ) = between(
             basal_start_times,
             basal_rates,
             basal_minutes,
             boundary_date,
             end_date,
             repeat_interval=repeat_interval
             )

        return (start_times_1 + start_times_2,
                end_times_1 + end_times_2,
                basal_rates_1 + basal_rates_2
                )

    start_index = 0
    end_index = len(basal_start_times)

    for (i, start_time) in enumerate(basal_start_times):
        start_time = timedelta(
            hours=start_time.hour,
            minutes=start_time.minute,
            seconds=start_time.second
        )
        if start_offset >= start_time:
            start_index = i
        if end_offset < start_time:
            end_index = i
            break

    reference_date = start_date - start_offset
    reference_date = datetime(
        year=reference_date.year,
        month=reference_date.month,
        day=reference_date.day,
        hour=reference_date.hour,
        minute=reference_date.minute,
        second=reference_date.second,
        tzinfo=timezone_info
        )

    if start_index > end_index:
        return ([], [], [])

    (output_start_times, output_end_times, output_basal_rates) = ([], [], [])

    for i in range(start_index, end_index):
        end_time = (timedelta(
            hours=basal_start_times[i+1].hour,
            minutes=basal_start_times[i+1].minute,
            seconds=basal_start_times[i+1].second) if i+1 <
                    len(basal_start_times) else max_time_interval)

        output_start_times.append(
            reference_date + timedelta(
                hours=basal_start_times[i].hour,
                minutes=basal_start_times[i].minute,
                seconds=basal_start_times[i].second
            )
        )
        output_end_times.append(reference_date + end_time)
        output_basal_rates.append(basal_rates[i])

    assert len(output_start_times) == len(output_end_times) ==\
        len(output_basal_rates), "expected output shape to match"

    return (output_start_times, output_end_times, output_basal_rates)


def schedule_offset(date_to_offset, reference_time,
                    repeat_interval=24):
    """ Returns the time interval for a given date normalized to the span of
        the schedule items

    Arguments:
    date_to_offset -- datetime object of the date to convert
    reference_time -- time object that's the first basal dose time in
                      a basal schedule (typically midnight)
    repeat_interval -- the interval with which the basal schedule repeats

    Output:
    datetime timedelta object representing offset
    """
    reference_time_seconds = (reference_time.hour * 3600
                              + reference_time.minute * 60
                              + reference_time.second)
    interval = time_interval_since_reference_date(date_to_offset)

    return timedelta(seconds=(interval - reference_time_seconds)
                     % (repeat_interval * 60 * 60)
                     + reference_time_seconds)


def insulin_on_board(
        dose_types, start_dates, end_dates, values, scheduled_basal_rates, delivered_units,
        model,
        start=None,
        end=None,
        delay=10,
        delta=5
    ):
    """ Calculates the timeline of insulin remaining for a collection of doses

        This model allows us to specify time of peak activity, as well as
        duration, and provides activity and IOB decay functions

    Arguments:
    dose_types -- list of types of doses (basal, bolus, etc)
    start_dates -- list of datetime objects representing the dates
                   the doses started at
    end_dates -- list of datetime objects representing the dates
                   the doses ended at
    values -- list of insulin values for doses
    scheduled_basal_rates -- basal rates scheduled during the times of doses
    delivered_units -- units actually delivered by dose
    model -- list of insulin model parameters in format [DIA, peak_time]
    start -- datetime object of time to start calculating the IOB timeline
    end -- datetime object of time to end the IOB timeline
    delay -- the time to delay the dose effect
    delta -- the differential between timeline entries

    Output:
    Tuple in format (times_iob_was_calculated_at, iob_values (U of insulin))
    """
    assert len(dose_types) == len(start_dates) == len(end_dates) ==\
        len(values) == len(scheduled_basal_rates) == len(delivered_units),\
        "expected input shapes to match"

    if not dose_types:
        return ([], [])

    try:
        if len(model) == 1:
            (start, end
             ) = simulation_date_range_for_samples(
                 start_times=start_dates,
                 end_times=end_dates,
                 duration=model[0]*60,
                 delay=delay,
                 delta=delta
                 )
        else:
            (start, end
             ) = simulation_date_range_for_samples(
                 start_times=start_dates,
                 end_times=end_dates,
                 duration=model[0],
                 delay=delay,
                 delta=delta
                 )
    except IndexError:
        return ([], [])

    date = start
    iob_dates = []
    iob_values = []

    def find_partial_iob(i):
        return insulin_on_board_calc(
            dose_types[i],
            start_dates[i],
            end_dates[i],
            values[i],
            scheduled_basal_rates[i],
            delivered_units[i],
            date,
            model,
            delay,
            delta
            )

    while date <= end:
        iob_sum = 0
        for i in range(0, len(start_dates)):
            iob_sum += find_partial_iob(i)

        iob_dates.append(date)
        iob_values.append(iob_sum)
        date += timedelta(minutes=delta)

    assert len(iob_dates) == len(iob_values), "expected output shape to match"

    return (iob_dates, iob_values)


def insulin_on_board_calc(
        type_, start_date, end_date, value, scheduled_basal_rate, delivered_units,
        date,
        model,
        delay,
        delta
    ):
    """ Calculates the insulin on board for a specific dose at a specific time

    Arguments:
    type_ -- String with type of dose (bolus, basal, etc)
    start_date -- the date the dose started at (datetime object)
    end_date -- the date the dose ended at (datetime object)
    value -- insulin value for dose
    scheduled_basal_rate -- basal rate scheduled during the times of dose
                            (0 for a bolus)
    delivered_units -- units actually delivered by pump
    date -- date the IOB is being calculated (datetime object)
    model -- list of insulin model parameters in format [DIA, peak_time]
    delay -- the time to delay the dose effect
    delta -- the differential between timeline entries

    Output:
    IOB at date
    """
    time = time_interval_since(date, start_date)

    if start_date > end_date or time < 0:
        return 0

    if len(model) == 1:  # walsh model
        if time_interval_since(end_date, start_date) <= 1.05 * delta * 60:
            return net_basal_units(
                type_,
                value,
                start_date,
                end_date,
                scheduled_basal_rate,
                delivered_units,
                ) * walsh_percent_effect_remaining(
                    (time / 60 - delay),
                    model[0]
                    )
        # This will normally be for basals
        return net_basal_units(
            type_,
            value,
            start_date,
            end_date,
            scheduled_basal_rate,
            delivered_units) * continuous_delivery_insulin_on_board(
                start_date,
                end_date,
                date,
                model,
                delay,
                delta
                )

    # Consider doses within the delta time window as momentary
    # This will normally be for boluses or short temp basals
    if time_interval_since(end_date, start_date) <= 1.05 * delta * 60:
        return net_basal_units(
            type_,
            value,
            start_date,
            end_date,
            scheduled_basal_rate,
            delivered_units
            ) * percent_effect_remaining(
                (time / 60 - delay),
                model[0],
                model[1]
                )
    # This will normally be for basals
    return net_basal_units(
        type_,
        value,
        start_date,
        end_date,
        scheduled_basal_rate,
        delivered_units) * continuous_delivery_insulin_on_board(
            start_date,
            end_date,
            date,
            model,
            delay,
            delta
            )


def continuous_delivery_insulin_on_board(
        start_date,
        end_date,
        at_date,
        model,
        delay,
        delta
    ):
    """ Calculates the percent of original insulin that is still on board
         at a specific time for a dose given over a period greater than
         1.05x the delta (this will almost always be a basal)

    Arguments:
    start_date -- the date the dose started at (datetime object)
    end_date -- the date the dose ended at (datetime object)
    at_date -- date the IOB is being calculated (datetime object)
    model -- list of insulin model parameters in format [DIA, peak_time]
    delay -- the time to delay the dose effect
    delta -- the differential between timeline entries

    Output:
    Percentage of insulin remaining at the at_date
    """
    dose_duration = time_interval_since(end_date, start_date)
    delay *= 60
    delta *= 60

    if dose_duration < 0:
        return 0

    time = time_interval_since(at_date, start_date)
    iob = 0
    dose_date = 0

    while (dose_date <= min(floor((time + delay) / delta) * delta,
                            dose_duration)):
        if dose_duration > 0:
            segment = (max(
                0,
                min(dose_date + delta,
                    dose_duration
                    )
                - dose_date) / dose_duration)
        else:
            segment = 1
        if len(model) == 1:  # if walsh model
            iob += segment * walsh_percent_effect_remaining(
                (time - delay - dose_date) / 60,
                model[0]
                )
        else:
            iob += segment * percent_effect_remaining(
                (time - delay - dose_date) / 60,
                model[0],
                model[1]
                )
        dose_date += delta

    return iob


def glucose_effects(
        dose_types,
        dose_start_dates,
        dose_end_dates,
        dose_values,
        scheduled_basal_rates,
        delivered_units,
        model,
        sensitivity_start_times,
        sensitivity_end_times,
        sensitivity_values,
        delay=10,
        delta=5,
        start=None,
        end=None
        ):
    """ Calculates the timeline of glucose effects for a collection of doses

    Arguments:
    dose_types -- list of types of doses (basal, bolus, etc)
    dose_start_dates -- list of datetime objects representing the dates
                       the doses started at
    dose_end_dates -- list of datetime objects representing the dates
                       the doses ended at
    dose_values -- list of insulin values for doses
    scheduled_basal_rates -- basal rates scheduled during the times of doses

    model -- list of insulin model parameters in format [DIA, peak_time] if
             exponential model, or [DIA] if Walsh model

    sensitivity_start_times -- list of time objects of start times of
                               given insulin sensitivity values
    sensitivity_end_times -- list of time objects of start times of
                             given insulin sensitivity values
    sensitivity_values -- list of sensitivities (mg/dL/U)

    delay -- the time to delay the dose effect
    delta -- the differential between timeline entries

    start -- datetime to start calculating the effects at
    end -- datetime to end calculation of effects

    Output:
    Tuple in format (times_glucose_effect_was_calculated_at,
                     glucose_effect_values (mg/dL))
    """
    assert len(dose_types) == len(dose_start_dates) == len(dose_end_dates)\
        == len(dose_values) == len(scheduled_basal_rates) == len(delivered_units),\
        "expected input shapes to match"

    if not dose_types and not (start is not None and end is not None):
        return ([], [])

    if len(model) == 1:  # if using a Walsh model
        start, end = simulation_date_range_for_samples(
            start_times=dose_start_dates,
            end_times=dose_end_dates,
            duration=model[0] * 60,
            delay=delay,
            delta=delta,
            start=start,
            end=end
        )
    else:
        start, end = simulation_date_range_for_samples(
            start_times=dose_start_dates,
            end_times=dose_end_dates,
            duration=model[0],
            delay=delay,
            delta=delta,
            start=start,
            end=end
        )

    date = start
    effect_dates = []
    effect_values = []

    def find_partial_effect(i):
        sensitivity = find_ratio_at_time(
            sensitivity_start_times,
            sensitivity_end_times,
            sensitivity_values,
            dose_start_dates[i]
        )
        return glucose_effect(
            dose_types[i],
            dose_start_dates[i],
            dose_end_dates[i],
            dose_values[i],
            scheduled_basal_rates[i],
            delivered_units[i],
            date,
            model,
            sensitivity,
            delay,
            delta
        )

    while date <= end:
        effect_sum = 0
        for i in range(0, len(dose_start_dates)):
            effect_sum += find_partial_effect(i)

        effect_dates.append(date)
        effect_values.append(effect_sum)
        date += timedelta(minutes=delta)

    assert len(effect_dates) == len(effect_values),\
        "expected output shapes to match"
    return (effect_dates, effect_values)


def find_ratio_at_time(ratio_start_times, ratio_end_times,
                       ratio_values, time_to_check
                       ):
    """ Finds ratio or correction range value at a given time

    Arguments:
    ratio_start_times -- list of time objects of start times of
                               given ratio/correction range values
    ratio_end_times -- list of time objects of start times of
                             given ratio/correction range values
    ratio_values -- list of ratio/correction range values
    time_to_check -- finding the value at this (date)time

    Output:
    Value at time_to_check
    """

    assert len(ratio_start_times) == len(ratio_values),\
        "expected input shapes to match"

    for i in range(0, len(ratio_start_times)):
        if ratio_end_times:
            if is_time_between(
                    ratio_start_times[i],
                    ratio_end_times[i],
                    time_to_check
                    ):  # pylint: disable=C0330
                return ratio_values[i]
        else:
            if is_time_between(
                    ratio_start_times[i],
                    (ratio_start_times[i+1]
                     if i+1 < len(ratio_start_times)
                     else ratio_start_times[0]
                    ),
                    time_to_check
                    ):  # pylint: disable=C0330
                return ratio_values[i]
    return 0


def is_time_between(start, end, time_to_check):
    """ Check if time is within an interval

    Arguments:
    start -- time (or datetime) of start of interval
    end -- time (or datetime) of end of interval
    time_to_check -- see if this time (or datetime) value is within the
                     interval

    Output:
    True if within interval, False if not
    """
    # convert from datetime to time if needed so we can compare
    if isinstance(start, datetime):
        start = start.time()
    if isinstance(end, datetime):
        end = end.time()
    if isinstance(time_to_check, datetime):
        time_to_check = time_to_check.time()

    if start < end:
        return start <= time_to_check <= end
    # if it crosses midnight
    return time_to_check >= start or time_to_check <= end


def glucose_effect(
        dose_type,
        dose_start_date,
        dose_end_date,
        dose_value,
        scheduled_basal_rate,
        delivered_units,
        date,
        model,
        insulin_sensitivity,
        delay,
        delta
    ):
    """ Calculates the timeline of glucose effects for a specific dose

    Arguments:
    dose_type -- types of dose (basal, bolus, etc)
    dose_start_date -- datetime object representing date doses start at
    dose_end_date -- datetime object representing date dose ended at
    dose_value -- insulin value for dose
    scheduled_basal_rate -- basal rate scheduled during the time of dose
    date -- datetime object of time to calculate the effect at
    insulin_sensitivity -- sensitivity (mg/dL/U)
    delay -- the time to delay the dose effect
    delta -- the differential between timeline entries

    Output:
    Glucose effect (mg/dL)
    """
    time = time_interval_since(date, dose_start_date)
    delay *= 60
    delta *= 60

    if time < 0:
        return 0

    # Consider doses within the delta time window as momentary
    # This will normally be for boluses
    if time_interval_since(
                dose_end_date,
                dose_start_date
            ) <= 1.05 * delta:  # pylint: disable=C0330

        if len(model) == 1:  # walsh model
            return net_basal_units(
                dose_type, dose_value,
                dose_start_date,
                dose_end_date,
                scheduled_basal_rate,
                delivered_units
                ) * -insulin_sensitivity * (1 - walsh_percent_effect_remaining(
                    (time - delay) / 60,
                    model[0]
                    ))

        return net_basal_units(
            dose_type,
            dose_value,
            dose_start_date,
            dose_end_date,
            scheduled_basal_rate,
            delivered_units
            ) * -insulin_sensitivity * (1 - percent_effect_remaining(
                (time - delay) / 60,
                model[0],
                model[1]
                ))
    # This will normally be for basals, and handles Walsh model automatically
    return net_basal_units(
        dose_type,
        dose_value,
        dose_start_date,
        dose_end_date,
        scheduled_basal_rate,
        delivered_units
        ) * -insulin_sensitivity * continuous_delivery_glucose_effect(
            dose_start_date,
            dose_end_date,
            date,
            model,
            delay / 60,
            delta / 60
            )


def continuous_delivery_glucose_effect(
        dose_start_date, dose_end_date,
        at_date,
        model,
        delay,
        delta
    ):
    """ Calculates the percent of glucose effect at a specific time for
        a dose given over a period greater than 1.05x the delta
        (this will almost always be a basal)

    Arguments:
    dose_start_date -- the date the dose started at (datetime object)
    dose_end_date -- the date the dose ended at (datetime object)
    at_date -- date the IOB is being calculated (datetime object)
    model -- list of insulin model parameters in format [DIA, peak_time]
    delay -- the time to delay the dose effect
    delta -- the differential between timeline entries

    Output:
    Percentage of insulin remaining at the at_date
    """
    dose_duration = time_interval_since(dose_end_date, dose_start_date)
    delay *= 60
    delta *= 60

    if dose_duration < 0:
        return 0

    time = time_interval_since(at_date, dose_start_date)
    activity = 0
    dose_date = 0

    while (dose_date <= min(
            floor((time + delay) / delta) * delta,
            dose_duration)):
        if dose_duration > 0:
            segment = (max(0,
                           min(dose_date + delta,
                               dose_duration
                               )
                           - dose_date
                           ) / dose_duration
                      )
        else:
            segment = 1

        if len(model) == 1:  # if walsh model
            activity += segment * (1 - walsh_percent_effect_remaining(
                (time - delay - dose_date) / 60,
                model[0])
                                  )

        else:
            activity += segment * (1 - percent_effect_remaining(
                (time - delay - dose_date) / 60,
                model[0],
                model[1]
                )
                                  )
        dose_date += delta

    return activity


def trim(
        dose_type, start, end, value, scheduled_basal_rate, delivered_units,
        start_interval=None,
        end_interval=None
    ):
    """ Trim doses to be within a particular interval

    Arguments:
    dose_type -- type of dose (basal, bolus, etc)
    start -- datetime object of time dose started at
    end -- datetime object of time dose ended at
    value -- amount, in U/hr (if a basal) or U (if bolus) of insulin in dose
    scheduled_basal_rate -- scheduled basal rate at the dose time
    start_interval -- start of interval to trim dose (datetime object)
    end_interval -- end of interval to trim dose (datetime object)

    Output:
    List with dose properties, trimmed to be in range (start_interval,
    end_interval). Format: [dose_type, dose_start_date, dose_end_date,
                            dose_value, dose_scheduled_rate]
    """
    if start.tzinfo:
        start_date = max(start_interval or DISTANT_PAST, start)
    else:
        start_date = max(start_interval or DISTANT_PAST, start)

    if end.tzinfo:
        return [dose_type,
                start_date,
                max(start_date,
                    min(end_interval or TIMEZONE_DISTANT_FUTURE, end)
                    ),
                value,
                scheduled_basal_rate,
                delivered_units
                ]

    return [dose_type,
            start_date,
            max(start_date, min(end_interval or DISTANT_FUTURE, end)),
            value,
            scheduled_basal_rate,
            delivered_units
            ]


def overlay_basal_schedule(
        dose_types, starts, ends, values,
        basal_start_times, basal_rates, basal_minutes,
        starting_at, ending_at,
        inserting_basal_entries
    ):
    """ Applies the current basal schedule to a collection of reconciled doses
        in chronological order

    Arguments:
    dose_types -- types of doses (basal, bolus, etc)
    starts -- datetime objects of times doses started at
    ends -- datetime objects of times doses ended at
    values -- amounts, in U/hr (if a basal) or U (if bolus) of insulin in doses
    basal_start_times -- list of times the basal rates start at
    basal_rates -- list of basal rates(U/hr)
    basal_minutes -- list of basal lengths (in mins)
    starting_at -- start of interval to overlay the basal schedule
                   (datetime object)
    ending_at -- end of interval to overlay the basal schedule
                 (datetime object)
    inserting_basal_entries -- whether basal doses should be created from the
                               schedule. Pass true only for pump models that do
                               not report their basal rates in event history.

    Output:
    Tuple with dose properties in range (start_interval,
    end_interval), overlayed with the basal schedule. It returns *four* dose
    properties, and does *not* return scheduled_basal_rates
    """
    assert len(dose_types) == len(starts) == len(ends) == len(values),\
        "expected input shapes to match"

    (out_dose_types, out_starts, out_ends, out_values) = ([], [], [], [])

    last_basal = []
    if inserting_basal_entries:
        last_basal = [DoseType.tempbasal,
                      starting_at,
                      starting_at,
                      0
                      ]

    for (i, type_) in enumerate(dose_types):
        if type_ in [DoseType.tempbasal, DoseType.basal, DoseType.suspend]:
            if ending_at and ends[i] > ending_at:
                continue

            if last_basal:
                if inserting_basal_entries:
                    (sched_basal_starts,
                     sched_basal_ends,
                     sched_basal_rates
                     ) = between(
                         basal_start_times,
                         basal_rates,
                         basal_minutes,
                         last_basal[2],
                         starts[i]
                         )
                    for j in range(0, len(sched_basal_starts)):
                        start = max(last_basal[2],
                                    sched_basal_starts[j]
                                    )
                        end = min(starts[i],
                                  sched_basal_ends[j]
                                  )

                        if time_interval_since(end, start)\
                                < sys.float_info.epsilon:
                            continue

                        out_dose_types.append(DoseType.basal)
                        out_starts.append(start)
                        out_ends.append(end)
                        out_values.append(sched_basal_rates[j])

            last_basal = [dose_types[i], starts[i], ends[i], values[i]]

            if last_basal:
                out_dose_types.append(last_basal[0])
                out_starts.append(last_basal[1])
                out_ends.append(last_basal[2])
                out_values.append(last_basal[3])

        elif type_ == DoseType.resume:
            assert "No resume events should be present in reconciled doses"

        elif type_ == DoseType.bolus:
            out_dose_types.append(dose_types[i])
            out_starts.append(starts[i])
            out_ends.append(ends[i])
            out_values.append(values[i])

    assert len(out_dose_types) == len(out_starts) == len(out_ends)\
        == len(out_values), "expected output shape to match"

    return (out_dose_types, out_starts, out_ends, out_values)
