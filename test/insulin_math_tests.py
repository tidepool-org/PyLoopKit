#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 09:00:27 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKitTests/InsulinMathTests.swift
"""
# pylint: disable= R0201, C0111, W0105, W0612
# diable pylint warnings for "method could be function", String statement
# has no effect, unused variable (for tuple unpacking)
import unittest
from datetime import datetime
import path_grabber  # pylint: disable=unused-import
from loop_kit_tests import load_fixture
from insulin_math import dose_entries, is_continuous


class TestInsulinKitFunctions(unittest.TestCase):
    """ unittest class to run InsulinKit tests."""
    WITHIN = 30

    def load_reservoir_fixture(self, resource_name):
        """ Load reservior data from json file

        Arguments:
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

    def load_insulin_value_fixture(self, resource_name):
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

    def load_glucose_effect_fixture(self, resource_name):
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

    def load_basal_rate_schedule_fixture(self, resource_name):
        """ Load basal schedule from json file

        Arguments:
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

    """ Tests for dose_entries """
    def test_dose_entries_from_reservoir_values(self):
        (i_dates, i_volumes) = self.load_reservoir_fixture(
            "reservoir_history_with_rewind_and_prime_input")
        (out_dose_types, out_start_dates, out_end_dates, out_values,
         out_scheduled_basal_rates) = self.load_dose_fixture(
             "reservoir_history_with_rewind_and_prime_output")

        out_start_dates.reverse()
        out_end_dates.reverse()
        out_values.reverse()

        (dose_types, start_dates, end_dates, values) = dose_entries(
            i_dates, i_volumes)

        self.assertEqual(len(out_start_dates), len(start_dates))
        for i in range(0, len(out_start_dates)):
            self.assertEqual(out_start_dates[i], start_dates[i])
            self.assertEqual(out_end_dates[i], end_dates[i])
            self.assertAlmostEqual(out_values[i], values[i], 2)

    """ Tests for is_continuous """
    def test_continuous_reservoir_values(self):
        (i_dates, i_volumes) = self.load_reservoir_fixture(
            "reservoir_history_with_rewind_and_prime_input")
        self.assertTrue(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T16:40:00"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))

        # We don't assert whether it's "stale".
        self.assertTrue(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T16:40:00"),
            datetime.fromisoformat("2016-01-30T22:40:00"), self.WITHIN))
        self.assertTrue(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T16:40:00"),
            datetime.now(), self.WITHIN))

        # The values must extend the startDate boundary
        self.assertFalse(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T15:00:00"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))

        # (the boundary condition is GTE)
        self.assertTrue(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T16:00:42"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))

        # Rises in reservoir volume taint the entire range
        self.assertFalse(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T15:55:00"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))

        # Any values of 0 taint the entire range
        i_dates.append(datetime.fromisoformat("2016-01-30T20:37:00"))
        i_volumes.append(0)
        self.assertFalse(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T16:40:00"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))

        # As long as the 0 is within the date interval bounds
        self.assertTrue(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T16:40:00"),
            datetime.fromisoformat("2016-01-30T19:40:00"), self.WITHIN))

    def test_non_continuous_reservoir_values(self):
        (i_dates, i_volumes) = self.load_reservoir_fixture(
            "reservoir_history_with_continuity_holes")

        self.assertTrue(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T18:30:00"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))
        self.assertFalse(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T17:30:00"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))


if __name__ == '__main__':
    unittest.main()
