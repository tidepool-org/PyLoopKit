#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:16:42 2019

@author: annaquinlan
"""
# pylint: disable=C0111, C0200, R0201, W0105
from datetime import datetime, time, timedelta
import unittest

from dose_store import get_glucose_effects
from glucose_store import (get_recent_momentum_effects,
                           get_counteraction_effects)
from loop_kit_tests import load_fixture


class TestLoopDataManagerFunctions(unittest.TestCase):
    """ unittest class to run tests of functions that LoopDataManager uses."""
    MOMENTUM_DATE_INTERVAL = 15

    def load_glucose_data(self, resource_name):
        """ Load glucose values from json file

        Arguments:
        resource_name -- file name without the extension
        Output:
        2 lists in (date, glucose_value) format
        """
        data = load_fixture(resource_name, ".json")

        dates = [
            datetime.fromisoformat(dict_.get("date"))
            for dict_ in data
        ]

        glucose_values = [dict_.get("amount") for dict_ in data]

        assert len(dates) == len(glucose_values),\
            "expected output shape to match"

        return (dates, glucose_values)

    def load_insulin_data(self, resource_name):
        """ Load insulin dose data from json file

        Arguments:
        resource_name -- name of file without the extension

        Output:
        5 lists in (dose_type (basal/bolus/suspend), start_dates, end_dates,
                    values (in units/insulin), scheduled_basal_rates) format
        """
        data = load_fixture(resource_name, ".json")

        dose_types = [
            dict_.get("type") or "!" for dict_ in data
        ]
        start_dates = [
            datetime.fromisoformat(dict_.get("start_at"))
            for dict_ in data
        ]
        end_dates = [
            datetime.fromisoformat(dict_.get("end_at"))
            for dict_ in data
        ]
        values = [dict_.get("amount") for dict_ in data]

        scheduled_basal_rates = [
            dict_.get("scheduled") or 0 for dict_ in data
        ]

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

    def load_carb_data(self, resource_name):
        """ Load carb entries data from json file

        Arguments:
        resource_name -- name of file without the extension

        Output:
        3 lists in (carb_values, carb_start_dates, carb_absorption_times)
        format
        """
        data = load_fixture(resource_name, ".json")

        carb_values = [dict_.get("amount") for dict_ in data]
        start_dates = [
            datetime.fromisoformat(dict_.get("start_at"))
            for dict_ in data
        ]
        absorption_times = [
            dict_.get("absorption_time") if dict_.get("absorption_time")
            else None for dict_ in data
        ]

        return (start_dates, carb_values, absorption_times)

    def load_settings(self, resource_name):
        """ Load settings from json file """
        settings_dict = load_fixture(resource_name, ".json")

        return settings_dict

    def load_sensitivities(self, resource_name):
        """ Load insulin sensitivity schedule from json file

        Arguments:
        resource_name -- name of file without the extension

        Output:
        3 lists in (sensitivity_start_time, sensitivity_end_time,
                    sensitivity_value (mg/dL/U)) format
        """
        data = load_fixture(resource_name, ".json")

        start_times = [
            datetime.strptime(dict_.get("start"), "%H:%M:%S").time()
            for dict_ in data
        ]
        end_times = [
            datetime.strptime(dict_.get("end"), "%H:%M:%S").time()
            for dict_ in data
        ]
        values = [dict_.get("value") for dict_ in data]

        assert len(start_times) == len(end_times) == len(values),\
            "expected output shape to match"

        return (start_times, end_times, values)

    def load_carb_ratios(self, resource_name):
        """ Load carb ratios from json file

        Arguments:
        resource_name -- name of file without the extension

        Output:
        2 lists in (ratio_start_time, ratio (in units/insulin),
                    length_of_rate) format
        """
        schedule = load_fixture(resource_name, ".json")

        carb_sched_starts = [
            time.fromisoformat(dict_.get("start"))
            for dict_ in schedule
        ]
        carb_sched_ratios = [dict_.get("ratio") for dict_ in schedule]

        return (carb_sched_starts, carb_sched_ratios)

    def load_scheduled_basals(self, resource_name):
        """ Load basal schedule from json file

        Arguments:
        resource_name -- name of file without the extension

        Output:
        3 lists in (rate_start_time, rate (in units/hr),
                    length_of_rate) format
        """
        data = load_fixture(resource_name, ".json")

        start_times = [
            datetime.strptime(dict_.get("start"), "%H:%M:%S").time()
            for dict_ in data
        ]
        rates = [dict_.get("rate") for dict_ in data]
        minutes = [dict_.get("minutes") for dict_ in data]

        assert len(start_times) == len(rates) == len(minutes),\
            "expected output shape to match"

        return (start_times, rates, minutes)

    def load_glucose_effect_output(self, resource_name):
        """ Load glucose effects from json file

        Arguments:
        resource_name -- name of file without the extension

        Output:
        2 lists in (date, glucose_value) format
        """
        fixture = load_fixture(resource_name, ".json")

        dates = [
            datetime.fromisoformat(dict_.get("date"))
            for dict_ in fixture
        ]
        glucose_values = [dict_.get("amount") for dict_ in fixture]

        assert len(dates) == len(glucose_values),\
            "expected output shape to match"

        return (dates, glucose_values)

    def load_glucose_velocities(self, resource_name):
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


if __name__ == '__main__':
    unittest.main()
