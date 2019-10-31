#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKitTests/GlucoseMathTests.swift
"""
# pylint: disable=C0111, C0411, R0201, W0105, W0612, C0200
# diable pylint warnings for too many arguments/variables and missing docstring
import unittest
from datetime import datetime

from . import path_grabber  # pylint: disable=unused-import
from .loop_kit_tests import load_fixture
from pyloopkit.glucose_math import linear_momentum_effect, counteraction_effects


class TestGlucoseKitFunctions(unittest.TestCase):
    """ unittest class to run GlucoseKit tests."""

    def load_input_fixture(self, resource_name):
        """ Load input json file

        Arguments:
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
        providences = [dict_.get("provenance_identifier")
                       or "com.loopkit.LoopKitTests"
                       for dict_ in fixture]

        assert len(dates) == len(glucose_values) == len(display_onlys) ==\
            len(providences), "expected output shape to match"

        return (dates, glucose_values, display_onlys, providences)

    def load_output_fixture(self, resource_name):
        """ Load output json file

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

    def load_effect_velocity_fixture(self, resource_name):
        """ Load effect-velocity json file

        Arguments:
        resource_name -- name of file without the extension

        Output:
        3 lists in (start_date, end_date, glucose_effects) format
        """
        fixture = load_fixture(resource_name, ".json")

        start_dates = [datetime.fromisoformat(dict_.get("startDate"))
                       for dict_ in fixture]
        end_dates = [datetime.fromisoformat(dict_.get("endDate"))
                     for dict_ in fixture]
        glucose_effects = [dict_.get("value") for dict_ in fixture]

        assert len(start_dates) == len(end_dates) == len(glucose_effects),\
            "expected output shape to match"

        return (start_dates, end_dates, glucose_effects)

    """ Tests for linear_momentum_effect """
    def test_momentum_effect_for_bouncing_glucose(self):
        (i_date_list,
         i_glucose_list,
         display_list,
         providence_list
         ) = self.load_input_fixture(
             "momentum_effect_bouncing_glucose_input"
             )
        (expected_date_list,
         expected_glucose_list
         ) = self.load_output_fixture(
             "momentum_effect_bouncing_glucose_output"
             )

        (glucose_effect_dates,
         glucose_effect_values
         ) = linear_momentum_effect(
             i_date_list,
             i_glucose_list,
             display_list,
             providence_list
             )

        self.assertEqual(
            len(expected_date_list), len(glucose_effect_dates)
        )
        for i in range(0, len(expected_date_list)):
            self.assertEqual(
                expected_date_list[i], glucose_effect_dates[i]
            )
            self.assertAlmostEqual(
                glucose_effect_values[i], expected_glucose_list[i], 2
            )

    def test_momentum_effect_for_rising_glucose(self):
        (i_date_list,
         i_glucose_list,
         display_list,
         providence_list
         ) = self.load_input_fixture("momentum_effect_rising_glucose_input")

        (expected_date_list,
         expected_glucose_list
         ) = self.load_output_fixture("momentum_effect_rising_glucose_output")

        (glucose_effect_dates,
         glucose_effect_values
         ) = linear_momentum_effect(
             i_date_list,
             i_glucose_list,
             display_list,
             providence_list
             )

        self.assertEqual(
            len(expected_date_list), len(glucose_effect_dates)
        )
        for i in range(0, len(expected_date_list)):
            self.assertEqual(
                expected_date_list[i], glucose_effect_dates[i]
            )
            self.assertAlmostEqual(
                glucose_effect_values[i], expected_glucose_list[i], 2
            )

    def test_momentum_effect_for_rising_glucose_doubles(self):
        (i_date_list,
         i_glucose_list,
         display_list,
         providence_list
         ) = self.load_input_fixture(
             "momentum_effect_rising_glucose_double_entries_input"
             )
        (expected_date_list,
         expected_glucose_list
         ) = self.load_output_fixture(
             "momentum_effect_rising_glucose_output"
             )

        (glucose_effect_dates,
         glucose_effect_values
         ) = linear_momentum_effect(
             i_date_list,
             i_glucose_list,
             display_list,
             providence_list
             )

        self.assertEqual(
            len(expected_date_list), len(glucose_effect_dates)
        )
        for i in range(0, len(expected_date_list)):
            self.assertEqual(
                expected_date_list[i], glucose_effect_dates[i]
            )
            self.assertAlmostEqual(
                glucose_effect_values[i], expected_glucose_list[i], 2
            )

    def test_momentum_effect_for_falling_glucose(self):
        (i_date_list,
         i_glucose_list,
         display_list,
         providence_list
         ) = self.load_input_fixture("momentum_effect_falling_glucose_input")

        (expected_date_list,
         expected_glucose_list
         ) = self.load_output_fixture(
             "momentum_effect_falling_glucose_output"
             )

        (glucose_effect_dates,
         glucose_effect_values
         ) = linear_momentum_effect(
             i_date_list,
             i_glucose_list,
             display_list,
             providence_list
             )

        self.assertEqual(
            len(expected_date_list), len(glucose_effect_dates)
        )
        for i in range(0, len(expected_date_list)):
            self.assertEqual(
                expected_date_list[i], glucose_effect_dates[i]
            )
            self.assertAlmostEqual(
                glucose_effect_values[i], expected_glucose_list[i], 2
            )

    def test_momentum_effect_for_falling_glucose_duplicates(self):
        (i_date_list,
         i_glucose_list,
         display_list,
         providence_list
         ) = self.load_input_fixture(
             "momentum_effect_falling_glucose_duplicate_input"
             )
        (expected_date_list,
         expected_glucose_list
         ) = self.load_output_fixture(
             "momentum_effect_falling_glucose_output"
             )

        (glucose_effect_dates,
         glucose_effect_values
         ) = linear_momentum_effect(
             i_date_list,
             i_glucose_list,
             display_list,
             providence_list
             )

        self.assertEqual(
            len(expected_date_list), len(glucose_effect_dates)
        )
        for i in range(0, len(expected_date_list)):
            self.assertEqual(
                expected_date_list[i], glucose_effect_dates[i]
            )
            self.assertAlmostEqual(
                glucose_effect_values[i], expected_glucose_list[i], 2
            )

    def test_momentum_effect_for_stable_glucose(self):
        (i_date_list,
         i_glucose_list,
         display_list,
         providence_list
         ) = self.load_input_fixture("momentum_effect_stable_glucose_input")

        (expected_date_list,
         expected_glucose_list
         ) = self.load_output_fixture("momentum_effect_stable_glucose_output")

        (glucose_effect_dates,
         glucose_effect_values
         ) = linear_momentum_effect(
             i_date_list,
             i_glucose_list,
             display_list,
             providence_list
             )

        self.assertEqual(
            len(expected_date_list), len(glucose_effect_dates)
        )
        for i in range(0, len(expected_date_list)):
            self.assertEqual(
                expected_date_list[i], glucose_effect_dates[i]
            )
            self.assertAlmostEqual(
                glucose_effect_values[i], expected_glucose_list[i], 2
            )

    def test_momentum_effect_for_duplicate_glucose(self):
        (i_date_list,
         i_glucose_list,
         display_list,
         providence_list
         ) = self.load_input_fixture("momentum_effect_duplicate_glucose_input")

        glucose_effect_dates = linear_momentum_effect(
            i_date_list,
            i_glucose_list,
            display_list,
            providence_list
        )[0]

        self.assertEqual(
            0, len(glucose_effect_dates)
        )

    def test_momentum_effect_for_empty_glucose(self):
        glucose_effect_dates = linear_momentum_effect(
            [], [], [], []
        )[0]

        self.assertEqual(
            0, len(glucose_effect_dates)
        )

    def test_momentum_effect_for_spaced_expected_glucose(self):
        (i_date_list,
         i_glucose_list,
         display_list,
         providence_list
         ) = self.load_input_fixture(
             "momentum_effect_incomplete_glucose_input"
             )

        glucose_effect_dates = linear_momentum_effect(
            i_date_list,
            i_glucose_list,
            display_list,
            providence_list
        )[0]

        self.assertEqual(
            0, len(glucose_effect_dates)
        )

    def test_momentum_effect_for_too_few_glucose(self):
        (i_date_list,
         i_glucose_list,
         display_list,
         providence_list
         ) = self.load_input_fixture("momentum_effect_bouncing_glucose_input")

        glucose_effect_dates = linear_momentum_effect(
            i_date_list[0:1],
            i_glucose_list[0:1],
            display_list[0:1],
            providence_list[0:1]
        )[0]

        self.assertEqual(
            0, len(glucose_effect_dates)
        )

    def test_momentum_effect_for_display_only_glucose(self):
        (i_date_list,
         i_glucose_list,
         display_list,
         providence_list
         ) = self.load_input_fixture(
             "momentum_effect_display_only_glucose_input"
             )

        glucose_effect_dates = linear_momentum_effect(
            i_date_list,
            i_glucose_list,
            display_list,
            providence_list
        )[0]

        self.assertEqual(
            0, len(glucose_effect_dates)
        )

    def test_momentum_effect_for_mixed_provenance_glucose(self):
        (i_date_list,
         i_glucose_list,
         display_list,
         providence_list
         ) = self.load_input_fixture(
             "momentum_effect_mixed_provenance_glucose_input"
             )

        glucose_effect_dates = linear_momentum_effect(
            i_date_list,
            i_glucose_list,
            display_list,
            providence_list
        )[0]

        self.assertEqual(
            0, len(glucose_effect_dates)
        )

    """ Tests for counteraction_effects """
    def test_counteraction_effects_for_falling_glucose(self):
        (i_dates,
         i_glucoses,
         displays,
         provenances
         ) = self.load_input_fixture(
             "counteraction_effect_falling_glucose_input"
             )

        (effect_dates,
         effect_glucoses
         ) = self.load_output_fixture("momentum_effect_stable_glucose_output")

        (expected_start_dates,
         expected_end_dates,
         expected_velocities
         ) = self.load_effect_velocity_fixture(
             "counteraction_effect_falling_glucose_output"
             )

        (start_dates,
         end_dates,
         velocities
         ) = counteraction_effects(
             i_dates,
             i_glucoses,
             displays,
             provenances,
             effect_dates,
             effect_glucoses
             )

        self.assertEqual(
            len(expected_start_dates), len(start_dates)
        )
        for i in range(0, len(expected_start_dates)):
            self.assertEqual(
                expected_start_dates[i], start_dates[i]
            )
            self.assertAlmostEqual(
                expected_velocities[i], velocities[i], 2
            )

    def test_counteraction_effects_for_falling_glucose_duplicates(self):
        (i_dates,
         i_glucoses,
         displays,
         provenances
         ) = self.load_input_fixture(
             "counteraction_effect_falling_glucose_double_entries_input"
             )

        (effect_dates,
         effect_glucoses
         ) = self.load_output_fixture(
             "counteraction_effect_falling_glucose_insulin"
             )

        (expected_start_dates,
         expected_end_dates,
         expected_velocities
         ) = self.load_effect_velocity_fixture(
             "counteraction_effect_falling_glucose_output"
             )

        (start_dates,
         end_dates,
         velocities
         ) = counteraction_effects(
             i_dates,
             i_glucoses,
             displays,
             provenances,
             effect_dates,
             effect_glucoses
             )

        self.assertEqual(
            len(expected_start_dates), len(start_dates)
        )
        for i in range(0, len(expected_start_dates)):
            self.assertEqual(
                expected_start_dates[i], start_dates[i]
            )
            self.assertAlmostEqual(
                expected_velocities[i], velocities[i], 2
            )

    def test_counteraction_effects_for_falling_glucose_almost_duplicates(self):
        (i_dates,
         i_glucoses,
         displays,
         provenances
         ) = self.load_input_fixture(
             "counteraction_effect_falling_glucose_almost_duplicates_input"
             )

        (effect_dates,
         effect_glucoses
         ) = self.load_output_fixture(
             "counteraction_effect_falling_glucose_insulin"
             )

        (expected_start_dates,
         expected_end_dates,
         expected_velocities
         ) = self.load_effect_velocity_fixture(
             "counteraction_effect_falling_glucose_almost_duplicates_output"
             )

        (start_dates,
         end_dates,
         velocities
         ) = counteraction_effects(
             i_dates,
             i_glucoses,
             displays,
             provenances,
             effect_dates,
             effect_glucoses
             )

        self.assertEqual(
            len(expected_start_dates), len(start_dates)
        )

        for i in range(0, len(expected_start_dates)):
            self.assertEqual(
                expected_start_dates[i], start_dates[i]
            )
            self.assertAlmostEqual(
                expected_velocities[i], velocities[i], 2
            )

    def test_counteraction_effects_for_no_glucose(self):
        (effect_dates,
         effect_glucoses
         ) = self.load_output_fixture(
             "counteraction_effect_falling_glucose_insulin"
             )

        (start_dates,
         end_dates,
         velocities
         ) = counteraction_effects(
             [], [], [], [],
             effect_dates,
             effect_glucoses
             )

        self.assertEqual(
            0, len(start_dates)
        )


if __name__ == '__main__':
    unittest.main()
