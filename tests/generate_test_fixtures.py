#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 14:25:03 2019

@author: annaquinlan
"""
# pylint: disable=C0200, R0914
from datetime import datetime, time
import json
from . import path_grabber  # pylint: disable=unused-import
from .loop_kit_tests import load_fixture
from pyloopkit.insulin_math import glucose_effects, insulin_on_board

WITHIN = 30

MODEL = [360, 75]
WALSH_MODEL = [4]

INSULIN_SENSITIVITY_START_DATES = [time(0, 0)]
INSULIN_SENSITIVITY_END_DATES = [time(23, 59)]
INSULIN_SENSITIVITY_VALUES = [40]


def load_dose_fixture(resource_name):
    """ Load dose from json file

    Arguments:
    resource_name -- name of file without the extension

    Output:
    5 lists in (dose_type (basal/bolus), start_dates, end_dates,
                values (in units/insulin), scheduled_basal_rates) format
    """
    fixture = load_fixture(resource_name, ".json")

    dose_types = [dict_.get("type") or "!" for dict_ in fixture]
    start_dates = [datetime.fromisoformat(dict_.get("start_at"))
                   for dict_ in fixture]
    end_dates = [datetime.fromisoformat(dict_.get("end_at"))
                 for dict_ in fixture]
    values = [dict_.get("amount") for dict_ in fixture]
    # not including description, unit, and raw bc not relevent
    scheduled_basal_rates = [dict_.get("scheduled") or 0
                             for dict_ in fixture]

    assert len(dose_types) == len(start_dates) == len(end_dates) ==\
        len(values) == len(scheduled_basal_rates),\
        "expected output shape to match"
    # if dose_type doesn't exist (meaning there's an "!"), remove entry
    if "!" in dose_types:
        for i in range(0, len(dose_types)):
            if dose_types[i] == "!":
                del dose_types[i]
                del start_dates[i]
                del end_dates[i]
                del values[i]
                del scheduled_basal_rates[i]

    return (dose_types, start_dates, end_dates, values,
            scheduled_basal_rates)


def load_glucose_effect_fixture(resource_name):
    """ Load glucose effects from json file

    Arguments:
    resource_name -- name of file without the extension

    Output:
    2 lists in (date, glucose_value) format
    """
    fixture = load_fixture(resource_name, ".json")

    dates = [datetime.fromisoformat(dict_.get("date"))
             for dict_ in fixture]
    glucose_values = [dict_.get("amount") for dict_ in fixture]

    assert len(dates) == len(glucose_values),\
        "expected output shape to match"
    return (dates, glucose_values)


def load_insulin_value_fixture(resource_name):
    """ Load insulin values from json file

    Arguments:
    resource_name -- name of file without the extension

    Output:
    2 lists in (start_date, insulin_amount) format
    """
    fixture = load_fixture(resource_name, ".json")

    start_dates = [datetime.fromisoformat(dict_.get("date"))
                   for dict_ in fixture]
    insulin_values = [dict_.get("value") for dict_ in fixture]

    assert len(start_dates) == len(insulin_values),\
        "expected output shape to match"

    return (start_dates, insulin_values)


def generate_glucose_effect_fixture(dose_fixture, previous_fixture=False,
                                    model_type="Exponential"):
    """ Generate a glucose effect fixture given a dose fixture and an
    optional fixture (for comparison purposes)

    Arguments:
    dose_fixture -- the dose fixture to use to generate the glucose effect
                    (without the ".json" ending)
    previous_fixture -- a glucose effect fixture to compare with the new
                        glucose effect (without the ".json" ending)
    model -- the model to use to generate the effect (either Walsh or
             Exponential); Walsh has a DIA of 4 hours (modify "WALSH_MODEL"
             if you want to change that), Exponential has DIA of 360 mins and
             peak at 75 mins (modify "MODEL" to change)
    """
    (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
     ) = load_dose_fixture(dose_fixture)

    sensitivity_start_dates = INSULIN_SENSITIVITY_START_DATES
    sensitivity_end_dates = INSULIN_SENSITIVITY_END_DATES
    sensitivity_values = INSULIN_SENSITIVITY_VALUES

    if model_type.lower() in ["walsh", "w", "walsh model"]:
        model = WALSH_MODEL
    else:
        model = MODEL

    effect_dates, effect_values = glucose_effects(
        i_types, i_start_dates, i_end_dates, i_values,
        i_scheduled_basal_rates, model, sensitivity_start_dates,
        sensitivity_end_dates, sensitivity_values)

    if previous_fixture:
        (out_dates, out_effect_values) = load_glucose_effect_fixture(
            previous_fixture)

        for i in range(0, len(out_effect_values)):
            print(out_dates[i], effect_dates[i])
            print(out_effect_values[i], effect_values[i])
            print()

        answer = input("Look OK? (y/n) ")
        if answer in ("no", "n"):
            return

    output = []
    for i in range(0, len(effect_values)):
        effect_dict = {}
        effect_dict["date"] = effect_dates[i].isoformat()
        effect_dict["unit"] = "mg/dL"
        effect_dict["amount"] = effect_values[i]
        output.append(effect_dict)

    if previous_fixture:
        json.dump(output, open(previous_fixture + "_new.json", "w"))
    else:
        json.dump(output, open(dose_fixture + "_output.json", "w"))


def generate_iob_fixture(dose_fixture, previous_iob_fixture=False,
                         model_type="Exponential"):
    """ Generate an IOB fixture given a dose fixture and an
    optional fixture (for comparison purposes)

    Arguments:
    dose_fixture -- the dose fixture to use to generate the glucose effect
                    (without the ".json" ending)
    previous_iob_fixture -- an old IOB fixture to compare with the new
                            IOB fixture (without the ".json" ending)
    model -- the model to use to generate the IOB (either Walsh or
             Exponential); Walsh has a DIA of 4 hours (modify "WALSH_MODEL"
             if you want to change that), Exponential has DIA of 360 mins and
             peak at 75 mins (modify "MODEL" to change)
    """
    (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
     ) = load_dose_fixture(dose_fixture)

    if model_type.lower() in ["walsh", "w", "walsh model"]:
        model = WALSH_MODEL
    else:
        model = MODEL

    (dates, insulin_values) = insulin_on_board(
        i_types, i_start_dates, i_end_dates, i_values,
        i_scheduled_basal_rates, model)

    if previous_iob_fixture:
        (out_dates, out_insulin_values) = load_insulin_value_fixture(
            previous_iob_fixture)

        for i in range(0, len(out_insulin_values)):
            print(out_dates[i], dates[i])
            print(out_insulin_values[i], insulin_values[i])
            print()

        answer = input("Look OK? (y/n) ")
        if answer in ("no", "n"):
            return

    output = []
    for i in range(0, len(insulin_values)):
        effect_dict = {}
        effect_dict["date"] = dates[i].isoformat()
        effect_dict["unit"] = "U"
        effect_dict["value"] = insulin_values[i]
        output.append(effect_dict)

    json.dump(output, open((str(previous_iob_fixture) if previous_iob_fixture
                            else model_type.lower() + "_iob_fixture")
                           + "_new.json", "w"))
