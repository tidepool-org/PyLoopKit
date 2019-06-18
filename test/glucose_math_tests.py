#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKitTests/GlucoseMathTests.swift
"""
# pylint: disable=C0111, C0411, R0201, W0105
# diable pylint warnings for too many arguments/variables and missing docstring
import unittest
import path_grabber  # pylint: disable=unused-import
from datetime import datetime
from loop_kit_tests import load_fixture
from glucose_math import linear_momentum_effect


class GlucoseFixtureValue:
    """ Constructs a glucose value for the purposes of running tests.

    Attributes:
    start_date -- date and time of glucose value
    quantity -- glucose value (mg/dL)
    is_display_only -- whether to do computations with
    provenance_identifier -- where value came from; defaults to
                                 com.loopkit.LoopKitTests
    """
    def __init__(self, start_date, quantity, is_display_only,
                 provenance_identifier):
        self.start_date = start_date
        self.quantity = quantity
        self.is_display_only = is_display_only
        self.provenance_identifier = (provenance_identifier
                                      or "com.loopkit.LoopKitTests")

    def __lt__(self, other):
        return self.start_date < other.start_date

    def __eq__(self, other):
        return (self.start_date == other.start_date and
                self.quantity == other.quantity and
                self.is_display_only == other.is_display_only and
                self.provenance_identifier == other.provenance_identifier)


class TestGlucoseKitFunctions(unittest.TestCase):
    """ unittest class to run GlucoseKit tests."""

    def load_input_fixture(self, resource_name):
        """ Load input json file

        Keyword arguments:
        resource_name -- name of file without the extension

        Variable names:
        fixture -- list of dictionaries; each dictionary contains properties
        of a GlucoseFixtureValue

        Output:
        4 lists in (date, glucose_value,
        display_only (for calibration purposes), providence_identifier) format
        """
        fixture = load_fixture(resource_name, ".json")

        dates = [datetime.fromisoformat(dict_.get("date"))
                 for dict_ in fixture]
        glucose_values = [dict_.get("amount") for dict_ in fixture]

        def get_boolean(dict_):
            return dict_.get("display_only") in ("yes", "true", "True")

        display_onlys = [get_boolean(dict_) for dict_ in fixture]
        providences = [dict_.get("provenance_identifier") or
                       "com.loopkit.LoopKitTests" for dict_ in fixture]

        assert len(dates) == len(glucose_values) == len(display_onlys) ==\
            len(providences), "expected output shape to match"

        return (dates, glucose_values, display_onlys, providences)

    def load_output_fixture(self, resource_name):
        """ Load output json file

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

    def load_effect_velocity_fixture(self, resource_name):
        """ Load effect-velocity json file

        Keyword arguments:
        resource_name -- name of file without the extension

        Output:
        3 lists in (start_date, end_date, glucose_effects) format
        """
        fixture = load_fixture(resource_name, ".json")

        start_dates = [datetime.fromisoformat(dict_.get("start_date"))
                       for dict_ in fixture]
        end_dates = [datetime.fromisoformat(dict_.get("end_date"))
                     for dict_ in fixture]
        glucose_effects = [dict_.get("value") for dict_ in fixture]

        assert len(start_dates) == len(end_dates) == len(glucose_effects),\
            "expected output shape to match"

        return (start_dates, end_dates, glucose_effects)

    """ Tests for linear_momentum_effect """
    def test_momentum_effect_for_bouncing_glucose(self):
        (i_date_list, i_glucose_list, display_list, providence_list) =\
            self.load_input_fixture("momentum_effect_bouncing_glucose" +
                                    "_input")
        (out_date_list, out_glucose_list) = self.load_output_fixture(
            "momentum_effect_bouncing_glucose_output")

        (glucose_effect_dates, glucose_effect_values) = linear_momentum_effect(
            i_date_list, i_glucose_list, display_list, providence_list)

        self.assertEqual(len(out_date_list), len(glucose_effect_dates))
        for i in range(0, len(out_date_list)):
            self.assertEqual(out_date_list[i], glucose_effect_dates[i])
            self.assertAlmostEqual(glucose_effect_values[i],
                                   out_glucose_list[i], 2)

    def test_momentum_effect_for_rising_glucose(self):
        (i_date_list, i_glucose_list, display_list, providence_list) =\
            self.load_input_fixture("momentum_effect_rising_glucose" +
                                    "_input")
        (out_date_list, out_glucose_list) = self.load_output_fixture(
            "momentum_effect_rising_glucose_output")

        (glucose_effect_dates, glucose_effect_values) = linear_momentum_effect(
            i_date_list, i_glucose_list, display_list, providence_list)

        self.assertEqual(len(out_date_list), len(glucose_effect_dates))
        for i in range(0, len(out_date_list)):
            self.assertEqual(out_date_list[i], glucose_effect_dates[i])
            self.assertAlmostEqual(glucose_effect_values[i],
                                   out_glucose_list[i], 2)

    def test_momentum_effect_for_rising_glucose_doubles(self):
        (i_date_list, i_glucose_list, display_list, providence_list) =\
            self.load_input_fixture("momentum_effect_rising_glucose" +
                                    "_double_entries_input")
        (out_date_list, out_glucose_list) = self.load_output_fixture(
            "momentum_effect_rising_glucose_output")

        (glucose_effect_dates, glucose_effect_values) = linear_momentum_effect(
            i_date_list, i_glucose_list, display_list, providence_list)

        self.assertEqual(len(out_date_list), len(glucose_effect_dates))
        for i in range(0, len(out_date_list)):
            self.assertEqual(out_date_list[i], glucose_effect_dates[i])
            self.assertAlmostEqual(glucose_effect_values[i],
                                   out_glucose_list[i], 2)

    def test_momentum_effect_for_falling_glucose(self):
        (i_date_list, i_glucose_list, display_list, providence_list) =\
            self.load_input_fixture("momentum_effect_falling_glucose_input")
        (out_date_list, out_glucose_list) = self.load_output_fixture(
            "momentum_effect_falling_glucose_output")

        (glucose_effect_dates, glucose_effect_values) = linear_momentum_effect(
            i_date_list, i_glucose_list, display_list, providence_list)

        self.assertEqual(len(out_date_list), len(glucose_effect_dates))
        for i in range(0, len(out_date_list)):
            self.assertEqual(out_date_list[i], glucose_effect_dates[i])
            self.assertAlmostEqual(glucose_effect_values[i],
                                   out_glucose_list[i], 2)

    def test_momentum_effect_for_falling_glucose_duplicates(self):
        (i_date_list, i_glucose_list, display_list, providence_list) =\
            self.load_input_fixture("momentum_effect_falling_glucose_duplicate"
                                    + "_input")
        (out_date_list, out_glucose_list) = self.load_output_fixture(
            "momentum_effect_falling_glucose_output")

        (glucose_effect_dates, glucose_effect_values) = linear_momentum_effect(
            i_date_list, i_glucose_list, display_list, providence_list)

        self.assertEqual(len(out_date_list), len(glucose_effect_dates))
        for i in range(0, len(out_date_list)):
            self.assertEqual(out_date_list[i], glucose_effect_dates[i])
            self.assertAlmostEqual(glucose_effect_values[i],
                                   out_glucose_list[i], 2)

    def test_momentum_effect_for_stable_glucose(self):
        (i_date_list, i_glucose_list, display_list, providence_list) =\
            self.load_input_fixture("momentum_effect_stable_glucose_input")
        (out_date_list, out_glucose_list) = self.load_output_fixture(
            "momentum_effect_stable_glucose_output")

        (glucose_effect_dates, glucose_effect_values) = linear_momentum_effect(
            i_date_list, i_glucose_list, display_list, providence_list)

        self.assertEqual(len(out_date_list), len(glucose_effect_dates))
        for i in range(0, len(out_date_list)):
            self.assertEqual(out_date_list[i], glucose_effect_dates[i])
            self.assertAlmostEqual(glucose_effect_values[i],
                                   out_glucose_list[i], 2)

    def test_momentum_effect_for_duplicate_glucose(self):
        (i_date_list, i_glucose_list, display_list, providence_list) =\
            self.load_input_fixture("momentum_effect_duplicate_glucose_input")

        glucose_effect_dates = linear_momentum_effect(
            i_date_list, i_glucose_list, display_list, providence_list)[0]

        self.assertEqual(0, len(glucose_effect_dates))

    def test_momentum_effect_for_empty_glucose(self):
        (i_date_list, i_glucose_list, display_list, providence_list) =\
            ([], [], [], [])

        glucose_effect_dates = linear_momentum_effect(
            i_date_list, i_glucose_list, display_list, providence_list)[0]

        self.assertEqual(0, len(glucose_effect_dates))

    def test_momentum_effect_for_spaced_out_glucose(self):
        (i_date_list, i_glucose_list, display_list, providence_list) =\
            self.load_input_fixture("momentum_effect_incomplete_glucose_input")

        glucose_effect_dates = linear_momentum_effect(
            i_date_list, i_glucose_list, display_list, providence_list)[0]

        self.assertEqual(0, len(glucose_effect_dates))

    def test_momentum_effect_for_too_few_glucose(self):
        (i_date_list, i_glucose_list, display_list, providence_list) =\
            self.load_input_fixture("momentum_effect_bouncing_glucose_input")

        glucose_effect_dates = linear_momentum_effect(
            i_date_list[0:1], i_glucose_list[0:1], display_list[0:1],
            providence_list[0:1])[0]

        self.assertEqual(0, len(glucose_effect_dates))

    def test_momentum_effect_for_display_only_glucose(self):
        (i_date_list, i_glucose_list, display_list, providence_list) =\
            self.load_input_fixture("momentum_effect_display_only_glucose"
                                    + "_input")

        glucose_effect_dates = linear_momentum_effect(
            i_date_list, i_glucose_list, display_list, providence_list)[0]

        self.assertEqual(0, len(glucose_effect_dates))

    def test_momentum_effect_for_mixed_provenance_glucose(self):
        (i_date_list, i_glucose_list, display_list, providence_list) =\
            self.load_input_fixture("momentum_effect_mixed_provenance_glucose"
                                    + "_input")

        glucose_effect_dates = linear_momentum_effect(
            i_date_list, i_glucose_list, display_list, providence_list)[0]

        self.assertEqual(0, len(glucose_effect_dates))


if __name__ == '__main__':
    unittest.main()
