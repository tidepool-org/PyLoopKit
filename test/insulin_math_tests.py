#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 09:00:27 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKitTests/InsulinMathTests.swift
"""
# pylint: disable= R0201
# diable pylint warnings for "method could be function"
import unittest
from datetime import datetime
import path_grabber  # pylint: disable=unused-import
from loop_kit_tests import load_fixture


class TestInsulinKitFunctions(unittest.TestCase):
    """ unittest class to run InsulinKit tests."""
    def load_reservoir_fixture(self, resource_name):
        """ Load reservior data from json file

        Keyword arguments:
        resource_name -- name of file without the extension

        Variable names:
        fixture -- list of dictionaries; each dictionary contains properties
        of a NewReserviorValue

        Output:
        2 lists in (date, units_given) format
        """
        fixture = load_fixture(resource_name, ".json")

        dates = [datetime.fromisoformat(dict_.get("date"))
                 for dict_ in fixture]
        unit_volumes = [dict_.get("amount") for dict_ in fixture]

        assert len(dates) == len(unit_volumes),\
            "expected output shape to match"

        return (dates, unit_volumes)

    def load_dose_fixture(self, resource_name):
        """ Load dose from json file

        Keyword arguments:
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

    def load_insulin_value_fixture(self, resource_name):
        """ Load insulin values from json file

        Keyword arguments:
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

    def load_glucose_effect_fixture(self, resource_name):
        """ Load glucose effects from json file

        Keyword arguments:
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

    def load_basal_rate_schedule_fixture(self, resource_name):
        """ Load basal schedule from json file

        Keyword arguments:
        resource_name -- name of file without the extension

        Output:
        3 lists in (rate_start_time, rate (in units/insulin),
                    length_of_rate) format
        """
        fixture = load_fixture(resource_name, ".json")

        start_times = [datetime.strptime(dict_.get("start"), "%H:%M:%S").time()
                       for dict_ in fixture]
        rates = [dict_.get("rate") for dict_ in fixture]
        minutes = [dict_.get("minutes") for dict_ in fixture]

        assert len(start_times) == len(rates) == len(minutes),\
            "expected output shape to match"

        return (start_times, rates, minutes)