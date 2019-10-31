#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 09:48:51 2019

@author: annaquinlan
"""
# pylint: disable=C0111, C0200, R0201, W0105, R0914, R0904
from datetime import datetime, time, timedelta
import unittest

from . import path_grabber  # pylint: disable=unused-import
from pyloopkit.carb_store import get_carb_glucose_effects, get_carbs_on_board
from pyloopkit.dose_store import get_glucose_effects
from pyloopkit.dose import DoseType
from pyloopkit.glucose_store import (
    get_recent_momentum_effects, get_counteraction_effects
)
from .loop_kit_tests import load_fixture
from pyloopkit.pyloop_parser import (
    load_momentum_effects, get_glucose_data
    )


class TestDataStoreFunctions(unittest.TestCase):
    """ unittest class to run tests of functions that LoopDataManager uses."""
    MOMENTUM_DATE_INTERVAL = 15

    INSULIN_SENSITIVITY_START_DATES = [time(0, 0)]
    INSULIN_SENSITIVITY_END_DATES = [time(23, 59)]
    INSULIN_SENSITIVITY_VALUES = [40]

    DEFAULT_ABSORPTION_TIMES = [60,
                                120,
                                240
                                ]

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
            DoseType.from_str(
                dict_.get("type")
            ) or "!" for dict_ in data
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

        assert len(dose_types) == len(start_dates) == len(end_dates) ==\
            len(values),\
            "expected output shape to match"
        # if dose_type doesn't exist (meaning there's an "!"), remove entry
        if "!" in dose_types:
            for i in range(0, len(dose_types)):
                if dose_types[i] == "!":
                    del dose_types[i]
                    del start_dates[i]
                    del end_dates[i]
                    del values[i]

        return (dose_types, start_dates, end_dates, values)

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

    def load_carb_ratios(self):
        """ Load carb ratios from json file

        Output:
        2 lists in (ratio_start_time, ratio (in units/insulin),
                    length_of_rate) format
        """
        schedule = load_fixture("read_carb_ratios", ".json").get("schedule")

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

        start_dates = [
            datetime.fromisoformat(
                dict_.get("startDate")
                if dict_.get("startDate") else dict_.get("start_at"))
            for dict_ in fixture
        ]
        end_dates = [
            datetime.fromisoformat(
                dict_.get("endDate")
                if dict_.get("endDate") else dict_.get("end_at"))
            for dict_ in fixture
        ]
        glucose_effects = [
            dict_.get("value") if dict_.get("value")
            else dict_.get("velocity") for dict_ in fixture
        ]
        assert len(start_dates) == len(end_dates) == len(glucose_effects),\
            "expected output shape to match"

        return (start_dates, end_dates, glucose_effects)

    def load_report_glucose_values(self, report_name):
        """ Load the cached glucose values from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("cached_glucose_samples"),\
            "expected issue report to contain glucose information"

        return get_glucose_data(
            report.get("cached_glucose_samples")
        )

    def load_report_momentum_effects(self, report_name):
        """ Load the expected momentum effects from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("glucose_momentum_effect"),\
            "expected issue report to contain momentum information"

        return load_momentum_effects(
            report.get("glucose_momentum_effect")
        )

    """ Tests for get_glucose_effects """
    def test_glucose_effects_walsh_bolus(self):
        time_to_calculate = datetime(2015, 7, 13, 11, 57, 37)

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
        time_to_calculate = datetime(2015, 7, 13, 11, 57, 37)

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
        time_to_calculate = datetime(2015, 7, 13, 12, 0, 0)

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
        time_to_calculate = datetime(2016, 2, 15, 14, 55, 0)
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

    def test_glucose_effects_walsh_long_basal(self):
        time_to_calculate = datetime(2015, 7, 13, 11, 40, 0)

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

    """ Tests for get_carbs_on_board """
    def test_non_dynamic_cob(self):
        carb_data = self.load_carb_data("carb_effect_from_history_input")
        (expected_dates,
         expected_values
         ) = self.load_glucose_data("carbs_on_board_output")

        (dates,
         values
         ) = get_carbs_on_board(
             *carb_data,
             datetime.fromisoformat("2015-10-15T18:45:00"),
             [], [], [],
             [], [],
             [], [], [],
             default_absorption_times=[120, 180, 240],
             absorption_time_overrun=1,
             delay=10,
             delta=5
             )

        self.assertEqual(
            len(expected_dates), len(dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], values[i], 1
            )

    def test_non_dynamic_cob_edgecases(self):
        carb_data = (
            [datetime.fromisoformat("2015-10-15T18:45:00")], [0], [120]
        )

        (dates,
         values
         ) = get_carbs_on_board(
             *carb_data,
             datetime.fromisoformat("2015-10-15T18:45:00"),
             [], [], [],
             [], [],
             [], [], [],
             default_absorption_times=[120, 180, 240],
             absorption_time_overrun=1,
             delay=10,
             delta=5
             )

        self.assertTrue(all(cob == 0 for cob in values))

        (dates,
         values
         ) = get_carbs_on_board(
             [], [], [],
             datetime.fromisoformat("2015-10-15T18:45:00"),
             [], [], [],
             [], [],
             [], [], [],
             default_absorption_times=[120, 180, 240],
             absorption_time_overrun=1,
             delay=10,
             delta=5
             )

        self.assertEqual(len(dates), 0)
        self.assertEqual(len(values), 0)

    def test_dynamic_cob_partial_absorption(self):
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
             "ice_35_min_partial_output"
             )

        (effect_dates,
         effect_values
         ) = get_carbs_on_board(
             carb_entry_starts, carb_entry_quantities, carb_entry_absorptions,
             datetime.fromisoformat("2015-10-15T21:35:00"),
             *input_ice,
             *carb_ratio_tuple,
             self.INSULIN_SENSITIVITY_START_DATES,
             self.INSULIN_SENSITIVITY_END_DATES,
             self.INSULIN_SENSITIVITY_VALUES,
             default_absorption_times,
             absorption_time_overrun=2,
             end_date=datetime.fromisoformat("2015-10-16T03:35:00")
             )

        self.assertEqual(len(expected_dates), len(effect_dates))

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], effect_values[i], 2
            )

    def test_dynamic_cob_edge_cases(self):
        input_ice = self.load_glucose_velocities("ice_slow_absorption")

        carb_data = ([], [], [])

        carb_ratio_tuple = self.load_carb_ratios()

        default_absorption_times = self.DEFAULT_ABSORPTION_TIMES

        (effect_dates,
         effect_values
         ) = get_carbs_on_board(
             *carb_data,
             input_ice[0][0] + timedelta(minutes=5),
             *input_ice,
             *carb_ratio_tuple,
             self.INSULIN_SENSITIVITY_START_DATES,
             self.INSULIN_SENSITIVITY_END_DATES,
             self.INSULIN_SENSITIVITY_VALUES,
             default_absorption_times,
             delay=10,
             delta=5,
             absorption_time_overrun=2,
             end_date=(
                 input_ice[0][0]
                 + timedelta(hours=18)
                 )
             )

        self.assertEqual(0, len(effect_dates))

        (effect_dates,
         effect_values
         ) = get_carbs_on_board(
             [input_ice[0][0]], [0], [120],
             input_ice[0][0] + timedelta(minutes=5),
             *input_ice,
             *carb_ratio_tuple,
             self.INSULIN_SENSITIVITY_START_DATES,
             self.INSULIN_SENSITIVITY_END_DATES,
             self.INSULIN_SENSITIVITY_VALUES,
             default_absorption_times,
             delay=10,
             delta=5,
             absorption_time_overrun=2,
             end_date=(
                 input_ice[0][0]
                 + timedelta(hours=18)
                 )
             )

        self.assertTrue(all(cob == 0 for cob in effect_values))


if __name__ == '__main__':
    unittest.main()
