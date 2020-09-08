#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 17:03:59 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/InsulinKit/DoseStore.swift
"""
# pylint: disable=R0913, R0914, C0200
from datetime import timedelta

from pyloopkit.dose_math import filter_date_range_for_doses
from pyloopkit.insulin_math import (annotated, trim, glucose_effects, reconciled)
from pyloopkit.loop_math import filter_date_range, sort_dose_lists


def get_glucose_effects(
        types, starts, ends, values, delivered_units,
        start_date,
        basal_starts, basal_rates, basal_minutes,
        sensitivity_starts, sensitivity_ends, sensitivity_values,
        insulin_model,
        delay=10,
        end_date=None
        ):
    """ Get the glucose effects at a particular time, given a list of
    doses and a time interval

    Arguments:
    types -- list of types of dose (basal, bolus, etc)
    starts -- start dates of the doses (datetime obj)
    ends -- end dates of the doses (datetime obj)
    values -- actual basal rates of doses in U/hr (if a basal)
             or the value of the boluses if in U
    delivered_units -- net Units of insulin actually delivered by a dose

    start_date -- date to start calculating glucose effects

    basal_starts -- list of times the basal rates start at
    basal_rates -- list of basal rates(U/hr)
    basal_minutes -- list of basal lengths (in mins)

    sensitivity_starts -- list of time objects of start times of
                          given insulin sensitivity values
    sensitivity_ends -- list of time objects of start times of
                        given insulin sensitivity values
    sensitivity_values -- list of sensitivities (mg/dL/U)

    insulin_model -- list in format [DIA (in hours)] if Walsh model, or
                     [DIA (minutes), peak (minutes)] if exponential model

    end_date -- date to stop calculating glucose effects

    Output:
    Glucose effects in the format (effect_date, effect_value)
    """
    assert len(types) == len(starts) == len(ends) == len(values) == len(delivered_units),\
        "expected input shapes to match"

    # to properly know glucose effects at start_date,
    # we need to go back another DIA hours
    if len(insulin_model) == 1:  # if using Walsh model
        dose_start = (start_date
                      - timedelta(
                          hours=insulin_model[0]
                          )
                      )
    else:
        dose_start = (start_date
                      - timedelta(
                          minutes=insulin_model[0]
                          )
                      )

    filtered_doses = filter_date_range_for_doses(
        types, starts, ends, values, delivered_units,
        dose_start,
        end_date
        )

    # reconcile the doses to get a cleaner data set
    # (add resumes for suspends and trim any overlapping temp basals)
    reconciled_doses = reconciled(
        *filtered_doses
        )
    # sort the lists because they could be slightly out of order due to
    # basals and suspends
    sorted_reconciled_doses = sort_dose_lists(*reconciled_doses)[0:5]

    # annotate the doses with scheduled basal rate
    (a_types,
     a_starts,
     a_ends,
     a_values,
     a_scheduled_rates,
     a_delivered_units
     ) = annotated(
         *sorted_reconciled_doses,
         basal_starts, basal_rates, basal_minutes,
         convert_to_units_hr=False
     )

    # trim the doses to start of interval
    for i in range(0, len(a_types)):
        result = trim(
            a_types[i], a_starts[i], a_ends[i], a_values[i], a_delivered_units[i],
            a_scheduled_rates[i],
            start_interval=dose_start
            )

        a_starts[i] = result[1]
        a_ends[i] = result[2]

    # get the glucose effects using the prepared dose data
    glucose_effect = glucose_effects(
        a_types, a_starts, a_ends, a_values, a_scheduled_rates, a_delivered_units,
        insulin_model,
        sensitivity_starts, sensitivity_ends, sensitivity_values,
        delay=delay,
        start=start_date,
        end=end_date
        )

    # don't return effects that are less than the start date or greater than
    # the end date (if there is one)
    (filtered_starts,
     ends,
     filtered_effect_values) = filter_date_range(
         glucose_effect[0],
         [],
         glucose_effect[1],
         start_date,
         end_date
         )

    return (filtered_starts, filtered_effect_values)
