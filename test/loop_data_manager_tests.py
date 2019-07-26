#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:16:42 2019

@author: annaquinlan
"""
# pylint: disable=C0111, C0200, R0201, W0105, R0914, R0904
from datetime import datetime, timedelta
import unittest

import path_grabber  # pylint: disable=unused-import
from carb_store import get_carb_glucose_effects
from dose_store import get_glucose_effects
from glucose_store import (
    get_recent_momentum_effects, get_counteraction_effects
)
from loop_data_manager import update_retrospective_glucose_effect
from loop_kit_tests import load_fixture
from loop_math import predict_glucose
from pyloop_parser import (
    load_momentum_effects, get_glucose_data, get_insulin_effects,
    get_normalized_insulin_data, get_basal_schedule, get_carb_ratios,
    get_sensitivities, get_settings, get_counteractions, get_carb_data,
    get_retrospective_effects
)


class TestLoopDataManagerFunctions(unittest.TestCase):
    """ unittest class to run integrated tests of LoopDataManager uses."""

    def load_report_glucose_values(self, report_name):
        """ Load the cached glucose values from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("cached_glucose_samples"),\
            "expected issue report to contain glucose information"

        return get_glucose_data(
            report.get("cached_glucose_samples")
        )

    def load_report_insulin_doses(self, report_name):
        """ Load the normalized dose entries from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("get_normalized_dose_entries"),\
            "expected issue report to contain dose information"

        return get_normalized_insulin_data(
            report.get("get_normalized_dose_entries")
        )

    def load_report_carb_values(self, report_name):
        """ Load the carb entries from an issue report """
        report = load_fixture(report_name, ".json")

        if not report.get("cached_carb_entries"):
            print("Issue report contains no carb information")
            return ([], [])

        return get_carb_data(
            report.get("cached_carb_entries")
        )

    def load_report_basal_schedule(self, report_name):
        """ Load the basal schedule from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("basal_rate_schedule"),\
            "expected issue report to contain basal rate information"

        return get_basal_schedule(
            report.get("basal_rate_schedule")
        )

    def load_report_cr_schedule(self, report_name):
        """ Load the carb ratio schedule from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("carb_ratio_schedule"),\
            "expected issue report to contain carb ratio information"

        return get_carb_ratios(
            report.get("carb_ratio_schedule")
        )

    def load_report_sensitivity_schedule(self, report_name):
        """ Load the insulin sensitivity schedule from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("insulin_sensitivity_factor_schedule"),\
            "expected issue report to contain insulin sensitivity information"

        return get_sensitivities(
            report.get("insulin_sensitivity_factor_schedule")
        )

    def load_report_settings(self, report_name):
        """ Load the relevent settings from an issue report """
        report = load_fixture(report_name, ".json")

        return get_settings(report)

    def load_report_momentum_effects(self, report_name):
        """ Load the expected momentum effects from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("glucose_momentum_effect"),\
            "expected issue report to contain momentum information"

        return load_momentum_effects(
            report.get("glucose_momentum_effect")
        )

    def load_report_glucose_values(self, report_name):
        """ Load the cached glucose values from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("cached_glucose_samples"),\
            "expected issue report to contain momentum information"

        return get_glucose_data(
            report.get("cached_glucose_samples")
        )

    """ Tests for get_glucose_effects """
    def test_glucose_effects_walsh_bolus(self):
        time_to_calculate = (
            datetime(2015, 7, 13, 12, 2, 37)
            - timedelta(hours=24)
        )
        (effect_dates,
         effect_values
         ) = get_glucose_effects(
             *self.load_insulin_data("bolus_dose"),
             time_to_calculate,
             *self.load_scheduled_basals("basal_schedule"),
             *self.load_sensitivities("insulin_sensitivity_schedule"),
             self.load_settings("walsh_settings").get("model")
             )

        (expected_dates,
         expected_values
         ) = self.load_glucose_effect_output(
             "effect_from_bolus_output"
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], effect_values[i], 0
            )

    def test_glucose_effects_exponential_bolus(self):
        time_to_calculate = (
            datetime(2015, 7, 13, 12, 2, 37)
            - timedelta(hours=24)
        )
        (effect_dates,
         effect_values
         ) = get_glucose_effects(
             *self.load_insulin_data("bolus_dose"),
             time_to_calculate,
             *self.load_scheduled_basals("basal_schedule"),
             *self.load_sensitivities("insulin_sensitivity_schedule"),
             self.load_settings("exponential_settings").get("model")
             )

        (expected_dates,
         expected_values
         ) = self.load_glucose_effect_output(
             "effect_from_bolus_output_exponential"
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], effect_values[i], 0
            )

    def test_glucose_effects_walsh_basal(self):
        time_to_calculate = (
            datetime(2015, 7, 13, 12, 0, 0)
            - timedelta(hours=24)
        )
        (effect_dates,
         effect_values
         ) = get_glucose_effects(
             *self.load_insulin_data("short_basal_dose"),
             time_to_calculate,
             *self.load_scheduled_basals("basal_schedule"),
             *self.load_sensitivities("insulin_sensitivity_schedule"),
             self.load_settings("walsh_settings").get("model")
             )

        (expected_dates,
         expected_values
         ) = self.load_glucose_effect_output(
             "short_basal_dose_output"
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], effect_values[i], 0
            )

    def test_glucose_effects_walsh_doses(self):
        time_to_calculate = (
            datetime(2016, 2, 15, 12, 0, 0)
            - timedelta(hours=24)
        )
        (effect_dates,
         effect_values
         ) = get_glucose_effects(
             *self.load_insulin_data("reconcile_history"),
             time_to_calculate,
             *self.load_scheduled_basals("basal_schedule"),
             *self.load_sensitivities("insulin_sensitivity_schedule"),
             self.load_settings("walsh_settings").get("model")
             )

        (expected_dates,
         expected_values
         ) = self.load_glucose_effect_output(
             "reconcile_history_effects_output"
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                # Expected dates had timezones
                expected_dates[i], effect_dates[i] - timedelta(hours=2)
            )
            self.assertAlmostEqual(
                expected_values[i], effect_values[i], delta=3
            )

    def test_glucose_effect_walsh_doses(self):
        time_to_calculate = (
            datetime(2015, 7, 13, 11, 40, 0)
            - timedelta(hours=24)
        )
        (effect_dates,
         effect_values
         ) = get_glucose_effects(
             *self.load_insulin_data("long_basal_dose"),
             time_to_calculate,
             *self.load_scheduled_basals("basal_schedule"),
             *self.load_sensitivities("insulin_sensitivity_schedule"),
             self.load_settings("walsh_settings").get("model")
             )

        (expected_dates,
         expected_values
         ) = self.load_glucose_effect_output(
             "long_basal_dose_output"
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                # Expected dates had timezones
                expected_dates[i], effect_dates[i] - timedelta(hours=2)
            )
            self.assertAlmostEqual(
                expected_values[i], effect_values[i], delta=3
            )

    """ Tests for get_recent_momentum_effects """
    def test_momentum_bouncing_glucose(self):
        glucose_data = self.load_glucose_data(
            "momentum_effect_bouncing_glucose_input"
            )
        (expected_dates,
         expected_values
         ) = self.load_glucose_data(
             "momentum_effect_bouncing_glucose_output"
             )

        # slice the "expected" arrays to adjust for the shorter duration
        # (15 mins vs 30 mins)
        expected_dates = expected_dates[0:5]
        expected_values = expected_values[0:5]

        (effect_dates,
         effect_values
         ) = get_recent_momentum_effects(
             *glucose_data,
             datetime.fromisoformat("2015-10-24T19:25:00"),
             datetime.fromisoformat("2015-10-25T19:25:00"),
             self.MOMENTUM_DATE_INTERVAL
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )
        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], effect_values[i], 2
            )

    def test_momentum_rising_glucose_doubles(self):
        glucose_data = self.load_glucose_data(
            "momentum_effect_rising_glucose_double_entries_input"
            )
        (expected_dates,
         expected_values
         ) = self.load_glucose_data(
             "momentum_effect_rising_glucose_output"
             )

        # slice the "expected" arrays to adjust for the shorter duration
        # (15 mins vs 30 mins)
        expected_dates = expected_dates[0:4]
        expected_values = expected_values[0:4]

        (effect_dates,
         effect_values
         ) = get_recent_momentum_effects(
             *glucose_data,
             datetime.fromisoformat("2015-10-24T19:15:00"),
             datetime.fromisoformat("2015-10-25T19:15:00"),
             self.MOMENTUM_DATE_INTERVAL
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )
        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], effect_values[i], 2
            )

    def test_momentum_spaced_glucose(self):
        glucose_data = self.load_glucose_data(
            "momentum_effect_incomplete_glucose_input"
            )

        effect_dates = get_recent_momentum_effects(
            *glucose_data,
            datetime.fromisoformat("2015-10-24T19:14:37"),
            datetime.fromisoformat("2015-10-25T19:14:37"),
            self.MOMENTUM_DATE_INTERVAL
            )[0]

        self.assertEqual(
            0, len(effect_dates)
        )

    def test_momentum_no_glucose(self):
        glucose_data = ([], [])

        effect_dates = get_recent_momentum_effects(
            *glucose_data,
            datetime.fromisoformat("2015-10-24T19:14:37"),
            datetime.fromisoformat("2015-10-25T19:14:37"),
            self.MOMENTUM_DATE_INTERVAL
            )[0]

        self.assertEqual(
            0, len(effect_dates)
        )

    def test_momentum_issue_report(self):
        glucose_data = self.load_report_glucose_values("loop_issue_report")

        (expected_starts,
         expected_values
         ) = self.load_report_momentum_effects("loop_issue_report")

        (starts, values) = get_recent_momentum_effects(
            *glucose_data,
            datetime.strptime(
                "2019-07-17 12:50:58 +0000",
                "%Y-%m-%d %H:%M:%S %z"
                ),
            datetime.strptime(
                "2019-07-18 12:50:58 +0000",
                "%Y-%m-%d %H:%M:%S %z"
                )
            )

        self.assertEqual(
            len(expected_starts), len(starts)
        )
        for i in range(0, len(expected_starts)):
            self.assertEqual(
                expected_starts[i], starts[i]
            )
            self.assertAlmostEqual(
                expected_values[i], values[i], 2
            )

    """ Tests for get_counteraction_effects """
    def test_counteraction_effects_for_falling_glucose(self):
        glucose_data = self.load_glucose_data(
            "counteraction_effect_falling_glucose_input"
            )

        momentum_effect = self.load_glucose_data(
            "momentum_effect_stable_glucose_output"
            )

        (expected_starts,
         expected_ends,
         expected_velocities
         ) = self.load_glucose_velocities(
             "counteraction_effect_falling_glucose_output"
             )

        (start_dates,
         end_dates,
         velocities
         ) = get_counteraction_effects(
             *glucose_data,
             datetime.fromisoformat("2015-10-25T19:15:00"),
             *momentum_effect
             )

        self.assertEqual(
            len(expected_starts), len(start_dates)
        )
        for i in range(0, len(expected_starts)):
            self.assertEqual(
                expected_starts[i], start_dates[i]
            )
            self.assertEqual(
                expected_ends[i], end_dates[i]
            )
            self.assertAlmostEqual(
                expected_velocities[i], velocities[i], 2
            )

    def test_counteraction_effects_for_falling_glucose_almost_duplicates(self):
        glucose_data = self.load_glucose_data(
            "counteraction_effect_falling_glucose_almost_duplicates_input"
            )

        momentum_effect = self.load_glucose_data(
            "counteraction_effect_falling_glucose_insulin"
            )

        (expected_starts,
         expected_ends,
         expected_velocities
         ) = self.load_glucose_velocities(
             "counteraction_effect_falling_glucose_almost_duplicates_output"
             )

        (start_dates,
         end_dates,
         velocities
         ) = get_counteraction_effects(
             *glucose_data,
             datetime.fromisoformat("2015-10-25T19:15:00"),
             *momentum_effect
             )

        self.assertEqual(
            len(expected_starts), len(start_dates)
        )
        for i in range(0, len(expected_starts)):
            self.assertEqual(
                expected_starts[i], start_dates[i]
            )
            self.assertEqual(
                expected_ends[i], end_dates[i]
            )
            self.assertAlmostEqual(
                expected_velocities[i], velocities[i], 2
            )

    def test_counteraction_effects_no_glucose(self):
        glucose_data = ([], [])

        momentum_effect = self.load_glucose_data(
            "counteraction_effect_falling_glucose_insulin"
            )

        start_dates = get_counteraction_effects(
            *glucose_data,
            datetime.fromisoformat("2015-10-25T19:15:00"),
            *momentum_effect
            )[0]

        self.assertEqual(
            0, len(start_dates)
        )

    """ Tests for get_carb_glucose_effects """
    def test_dynamic_glucose_effect_absorption_none_observed(self):
        input_ice = self.load_glucose_velocities("ice_35_min_input")

        (carb_starts,
         carb_values,
         carb_absorptions
         ) = self.load_carb_data("carb_entry_input")

        carb_ratio_tuple = self.load_carb_ratios()

        default_absorption_times = self.DEFAULT_ABSORPTION_TIMES

        carb_entry_starts = [carb_starts[2]]
        carb_entry_quantities = [carb_values[2]]
        carb_entry_absorptions = [carb_absorptions[2]]

        (expected_dates,
         expected_values
         ) = self.load_glucose_effect_output(
             "dynamic_glucose_effect_none_observed_output"
             )

        (effect_dates,
         effect_values
         ) = get_carb_glucose_effects(
             carb_entry_starts,
             carb_entry_quantities,
             carb_entry_absorptions,
             input_ice[0][0],
             *input_ice,
             *carb_ratio_tuple,
             self.INSULIN_SENSITIVITY_START_DATES,
             self.INSULIN_SENSITIVITY_END_DATES,
             self.INSULIN_SENSITIVITY_VALUES,
             default_absorption_times,
             delay=10,
             absorption_time_overrun=2,
             end_date=input_ice[0][0]+timedelta(hours=6)
             )

        assert len(expected_dates) == len(effect_dates)

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], effect_values[i], 2
            )

    def test_glucose_effect_absorption_partially_observed(self):
        input_ice = self.load_glucose_velocities("ice_35_min_input")

        (carb_starts,
         carb_values,
         carb_absorptions
         ) = self.load_carb_data("carb_entry_input")

        carb_ratio_tuple = self.load_carb_ratios()

        default_absorption_times = self.DEFAULT_ABSORPTION_TIMES

        carb_entry_starts = [carb_starts[0]]
        carb_entry_quantities = [carb_values[0]]
        carb_entry_absorptions = [carb_absorptions[0]]

        (expected_dates,
         expected_values
         ) = self.load_glucose_effect_output(
             "dynamic_glucose_effect_partially_observed_output"
             )

        (effect_dates,
         effect_values
         ) = get_carb_glucose_effects(
             carb_entry_starts,
             carb_entry_quantities,
             carb_entry_absorptions,
             input_ice[0][0],
             *input_ice,
             *carb_ratio_tuple,
             self.INSULIN_SENSITIVITY_START_DATES,
             self.INSULIN_SENSITIVITY_END_DATES,
             self.INSULIN_SENSITIVITY_VALUES,
             default_absorption_times,
             delay=10,
             absorption_time_overrun=2,
             end_date=input_ice[0][0]+timedelta(hours=6)
             )

        assert len(expected_dates) == len(effect_dates)

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], effect_values[i], 2
            )

    def test_dynamic_glucose_effect_absorption_fully_observed(self):
        input_ice = self.load_glucose_velocities("ice_1_hour_input")

        (carb_starts,
         carb_values,
         carb_absorptions
         ) = self.load_carb_data("carb_entry_input")

        carb_ratio_tuple = self.load_carb_ratios()

        default_absorption_times = self.DEFAULT_ABSORPTION_TIMES

        carb_entry_starts = [carb_starts[0]]
        carb_entry_quantities = [carb_values[0]]
        carb_entry_absorptions = [carb_absorptions[0]]

        (expected_dates,
         expected_values
         ) = self.load_glucose_effect_output(
             "dynamic_glucose_effect_fully_observed_output")

        (effect_dates,
         effect_values
         ) = get_carb_glucose_effects(
             carb_entry_starts,
             carb_entry_quantities,
             carb_entry_absorptions,
             input_ice[0][0],
             *input_ice,
             *carb_ratio_tuple,
             self.INSULIN_SENSITIVITY_START_DATES,
             self.INSULIN_SENSITIVITY_END_DATES,
             self.INSULIN_SENSITIVITY_VALUES,
             default_absorption_times,
             delay=10,
             absorption_time_overrun=2,
             end_date=input_ice[0][0]+timedelta(hours=6)
             )

        self.assertEqual(len(effect_values), len(expected_values))

        for i in range(0, len(effect_values)):
            self.assertAlmostEqual(
                expected_dates[i], effect_dates[i], 2
            )
            self.assertAlmostEqual(
                expected_values[i], effect_values[i], 2
            )


if __name__ == '__main__':
    unittest.main()
