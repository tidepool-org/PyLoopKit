#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:16:42 2019

@author: annaquinlan
"""
# pylint: disable=C0111, C0200, R0201, W0105, R0914, R0904
from datetime import datetime, time, timedelta
from copy import deepcopy
import unittest
import pytest
# from . import path_grabber  # pylint: disable=unused-import
from pyloopkit.dose import DoseType
from pyloopkit.loop_data_manager import (
    get_pending_insulin,
    update_retrospective_glucose_effect,
    update,
)
from .loop_kit_tests import load_fixture, find_root_path
from pyloopkit.pyloop_parser import (
    load_momentum_effects,
    get_glucose_data,
    load_insulin_effects,
    get_insulin_data,
    get_basal_schedule,
    get_carb_ratios,
    get_sensitivities,
    get_settings,
    get_counteractions,
    get_carb_data,
    get_retrospective_effects,
    parse_report_and_run,
)


class TestLoopDataManagerFunctions(unittest.TestCase):
    """ unittest class to run integrated tests of LoopDataManager uses."""

    def load_report_glucose_values(self, report_name):
        """ Load the cached glucose values from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get(
            "cached_glucose_samples"
        ), "expected issue report to contain glucose information"

        return get_glucose_data(report.get("cached_glucose_samples"))

    def load_report_insulin_doses(self, report_name):
        """ Load the normalized dose entries from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get(
            "get_normalized_dose_entries"
        ), "expected issue report to contain dose information"

        return get_insulin_data(report.get("get_normalized_dose_entries"))

    def load_report_carb_values(self, report_name):
        """ Load the carb entries from an issue report """
        report = load_fixture(report_name, ".json")

        if not report.get("cached_carb_entries"):
            print("Issue report contains no carb information")
            return ([], [])

        return get_carb_data(report.get("cached_carb_entries"))

    def load_report_basal_schedule(self, report_name):
        """ Load the basal schedule from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get(
            "basal_rate_schedule"
        ), "expected issue report to contain basal rate information"

        return get_basal_schedule(report.get("basal_rate_schedule"))

    def load_report_cr_schedule(self, report_name):
        """ Load the carb ratio schedule from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get(
            "carb_ratio_schedule"
        ), "expected issue report to contain carb ratio information"

        return get_carb_ratios(report.get("carb_ratio_schedule"))

    def load_report_sensitivity_schedule(self, report_name):
        """ Load the insulin sensitivity schedule from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get(
            "insulin_sensitivity_factor_schedule"
        ), "expected issue report to contain insulin sensitivity information"

        return get_sensitivities(report.get("insulin_sensitivity_factor_schedule"))

    def load_report_settings(self, report_name):
        """ Load the relevent settings from an issue report """
        report = load_fixture(report_name, ".json")

        return get_settings(report)

    def load_report_momentum_effects(self, report_name):
        """ Load the expected momentum effects from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get(
            "glucose_momentum_effect"
        ), "expected issue report to contain momentum information"

        return load_momentum_effects(report.get("glucose_momentum_effect"))

    def load_report_insulin_effects(self, report_name):
        """ Load the expected insulin effects from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get(
            "insulin_effect"
        ), "expected issue report to contain insulin effect information"

        return load_insulin_effects(report.get("insulin_effect"))

    def load_report_counteraction_effects(self, report_name):
        """ Load the expected counteraction effects from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get(
            "insulin_counteraction_effects"
        ), "expected issue report to contain counteraction effect information"

        return get_counteractions(report.get("insulin_counteraction_effects"))

    def load_report_carb_effects(self, report_name):
        """ Load the expected carb effects from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get(
            "carb_effect"
        ), "expected issue report to contain carb effect information"

        return load_insulin_effects(report.get("carb_effect"))

    def load_report_retrospective_effects(self, report_name):
        """ Load the expected retrospective effects from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get(
            "retrospective_glucose_effect"
        ), "expected issue report to contain retrospective effect information"

        return get_retrospective_effects(report.get("retrospective_glucose_effect"))

    def load_report_predicted_glucoses(self, report_name):
        """ Load the expected retrospective effects from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get(
            "predicted_glucose"
        ), "expected issue report to contain glucose prediction information"

        return load_insulin_effects(report.get("predicted_glucose"))

    def run_report_through_runner(self, report_name):
        """ Load the expected retrospective effects from an issue report """
        root = find_root_path(report_name, ".json")

        return parse_report_and_run(root + "/", report_name + ".json")

    """ Integrated tests for all the effects """
    @pytest.mark.skip(reason="Skipping as PyLoopKit is being deprecated")
    def test_loop_with_utc_issue_report(self):
        recommendation = self.run_report_through_runner("utc_issue_report")
        pyloop_predicted_glucoses = [
            recommendation.get("predicted_glucose_dates"),
            recommendation.get("predicted_glucose_values"),
        ]
        expected_predicted_glucoses = self.load_report_predicted_glucoses(
            "utc_issue_report"
        )

        # check that the predicted glucose values are the same
        self.assertEqual(
            len(pyloop_predicted_glucoses[0]), len(expected_predicted_glucoses[0])
        )
        for i in range(0, len(pyloop_predicted_glucoses[0])):
            self.assertEqual(
                pyloop_predicted_glucoses[0][i], expected_predicted_glucoses[0][i]
            )
            self.assertAlmostEqual(
                pyloop_predicted_glucoses[1][i], expected_predicted_glucoses[1][i], 1
            )

        # check that the basal and bolus recommendations are as-expected
        self.assertEqual(recommendation.get("recommended_temp_basal")[0], 1.1)
        self.assertEqual(recommendation.get("recommended_temp_basal")[1], 30)
        self.assertEqual(recommendation.get("recommended_bolus")[0], 0)

    def test_loop_with_timezoned_issue_report(self):
        recommendation = self.run_report_through_runner("timezoned_issue_report")
        pyloop_predicted_glucoses = [
            recommendation.get("predicted_glucose_dates"),
            recommendation.get("predicted_glucose_values"),
        ]
        expected_predicted_glucoses = self.load_report_predicted_glucoses(
            "timezoned_issue_report"
        )

        self.assertEqual(
            len(pyloop_predicted_glucoses[0]), len(expected_predicted_glucoses[0])
        )
        for i in range(0, len(pyloop_predicted_glucoses[0])):
            self.assertAlmostEqual(
                pyloop_predicted_glucoses[1][i], expected_predicted_glucoses[1][i], 1
            )

        # check that the basal and bolus recommendations are as-expected
        self.assertIsNone(recommendation.get("recommended_temp_basal"))
        self.assertEqual(recommendation.get("recommended_bolus")[0], 0)
        self.assertAlmostEqual(
            recommendation.get("recommended_bolus")[2][1], 66.6912, 1
        )

    def test_loop_with_high_glucose_issue_report(self):
        recommendation = self.run_report_through_runner(
            "high_bg_recommended_basal_and_bolus_report"
        )
        pyloop_predicted_glucoses = [
            recommendation.get("predicted_glucose_dates"),
            recommendation.get("predicted_glucose_values"),
        ]
        expected_predicted_glucoses = self.load_report_predicted_glucoses(
            "high_bg_recommended_basal_and_bolus_report"
        )

        for i in range(0, len(expected_predicted_glucoses[0])):
            self.assertAlmostEqual(
                pyloop_predicted_glucoses[1][i], expected_predicted_glucoses[1][i], 1
            )

        self.assertEqual(recommendation.get("recommended_temp_basal")[0], 1.2)
        self.assertEqual(recommendation.get("recommended_temp_basal")[1], 30)
        self.assertEqual(recommendation.get("recommended_bolus")[0], 0.15)

    def test_loop_with_one_basal_issue_report(self):
        recommendation = self.run_report_through_runner("one_basal_issue_report")
        pyloop_predicted_glucoses = [
            recommendation.get("predicted_glucose_dates"),
            recommendation.get("predicted_glucose_values"),
        ]
        expected_predicted_glucoses = self.load_report_predicted_glucoses(
            "one_basal_issue_report"
        )

        self.assertEqual(
            len(pyloop_predicted_glucoses[0]), len(expected_predicted_glucoses[0])
        )
        for i in range(0, len(pyloop_predicted_glucoses[0])):
            self.assertAlmostEqual(
                pyloop_predicted_glucoses[1][i], expected_predicted_glucoses[1][i], 1
            )
        self.assertIsNone(recommendation.get("recommended_temp_basal"))

    """ Tests for get_pending_insulin """

    def test_negative_pending_insulin(self):
        now_time = datetime.fromisoformat("2019-08-01T12:15:00")
        basal_schedule = self.load_report_basal_schedule("loop_issue_report")

        last_temporary_basal = [
            DoseType.tempbasal,
            datetime.fromisoformat("2019-08-01T12:00:00"),
            datetime.fromisoformat("2019-08-01T12:30:00"),
            0.1,
        ]

        pending_insulin = get_pending_insulin(
            now_time, *basal_schedule, last_temporary_basal
        )

        self.assertEqual(0, pending_insulin)

    def test_short_temp_pending_insulin(self):
        now_time = datetime.fromisoformat("2019-08-01T12:15:00")
        basal_schedule = self.load_report_basal_schedule("loop_issue_report")

        last_temporary_basal = [
            DoseType.tempbasal,
            datetime.fromisoformat("2019-08-01T12:00:00"),
            datetime.fromisoformat("2019-08-01T12:16:00"),
            1.3,
        ]

        pending_insulin = get_pending_insulin(
            now_time, *basal_schedule, last_temporary_basal
        )

        self.assertAlmostEqual(pending_insulin, 0.0075, 5)

        # add a pending bolus
        pending_insulin = get_pending_insulin(
            now_time, *basal_schedule, last_temporary_basal, 0.5
        )
        self.assertAlmostEqual(pending_insulin, 0.5075, 5)

    def test_pending_insulin_edge_cases(self):
        now_time = datetime.fromisoformat("2019-08-01T12:15:00")
        basal_schedule = self.load_report_basal_schedule("loop_issue_report")

        # when there's no temp basal
        last_temporary_basal = None
        pending_insulin = get_pending_insulin(
            now_time, *basal_schedule, last_temporary_basal
        )
        self.assertEqual(pending_insulin, 0)

        # when the temp basal has already expired
        last_temporary_basal = [
            DoseType.tempbasal,
            datetime.fromisoformat("2019-08-01T11:00:00"),
            datetime.fromisoformat("2019-08-01T11:16:00"),
            0.8,
        ]
        pending_insulin = get_pending_insulin(
            now_time, *basal_schedule, last_temporary_basal
        )

        self.assertEqual(pending_insulin, 0)

        # when it isn't actually a temporary basal
        last_temporary_basal = [
            "Bolus",
            datetime.fromisoformat("2019-08-01T12:00:00"),
            datetime.fromisoformat("2019-08-01T12:30:00"),
            5.3,
        ]
        pending_insulin = get_pending_insulin(
            now_time, *basal_schedule, last_temporary_basal
        )
        self.assertEqual(pending_insulin, 0)

        # when the start and end times are reversed
        last_temporary_basal = [
            DoseType.tempbasal,
            datetime.fromisoformat("2019-08-01T12:55:00"),
            datetime.fromisoformat("2019-08-01T12:40:00"),
            0.95,
        ]
        pending_insulin = get_pending_insulin(
            now_time, *basal_schedule, last_temporary_basal
        )
        self.assertEqual(pending_insulin, 0)

    """ Tests for update_retrospective_glucose_effect """

    def test_retrospective_glucose_effect_only_bolus(self):
        glucose_data = self.load_report_glucose_values("timezoned_issue_report")
        carb_effects = self.load_report_carb_effects("timezoned_issue_report")
        counteraction_effects = self.load_report_counteraction_effects(
            "timezoned_issue_report"
        )
        now_time = datetime.strptime(
            "2019-07-25 22:50:57 +0000", "%Y-%m-%d %H:%M:%S %z"
        )

        (expected_dates, expected_values) = self.load_report_retrospective_effects(
            "timezoned_issue_report"
        )

        (dates, values) = update_retrospective_glucose_effect(
            *glucose_data,
            *carb_effects,
            *counteraction_effects,
            recency_interval=15,
            retrospective_correction_grouping_interval=30,
            now_time=now_time
        )

        self.assertEqual(len(expected_dates), len(dates))

        for i in range(0, len(dates)):
            self.assertEqual(expected_dates[i], dates[i])
            self.assertAlmostEqual(expected_values[i], values[i], 2)

    def test_retrospective_glucose_effect_date_crossing(self):
        glucose_data = self.load_report_glucose_values("basal_and_bolus_report")
        carb_effects = self.load_report_carb_effects("basal_and_bolus_report")
        counteraction_effects = self.load_report_counteraction_effects(
            "basal_and_bolus_report"
        )
        now_time = datetime.strptime(
            "2019-07-29 17:06:59 +0000", "%Y-%m-%d %H:%M:%S %z"
        )

        (expected_dates, expected_values) = self.load_report_retrospective_effects(
            "basal_and_bolus_report"
        )

        (dates, values) = update_retrospective_glucose_effect(
            *glucose_data,
            *carb_effects,
            *counteraction_effects,
            recency_interval=15,
            retrospective_correction_grouping_interval=30,
            now_time=now_time
        )

        self.assertEqual(len(expected_dates), len(dates))

        for i in range(0, len(dates)):
            self.assertEqual(expected_dates[i], dates[i])
            self.assertAlmostEqual(expected_values[i], values[i], 2)

    def test_retrospective_glucose_effect_edgecases(self):
        # no counteraction effects
        glucose_data = self.load_report_glucose_values("basal_and_bolus_report")
        carb_effects = self.load_report_carb_effects("basal_and_bolus_report")
        counteraction_effects = ([], [], [])
        now_time = datetime.strptime(
            "2019-07-29 17:06:59 +0000", "%Y-%m-%d %H:%M:%S %z"
        )
        (dates, values) = update_retrospective_glucose_effect(
            *glucose_data,
            *carb_effects,
            *counteraction_effects,
            recency_interval=15,
            retrospective_correction_grouping_interval=30,
            now_time=now_time
        )

        self.assertEqual(0, len(dates))

        # it shouldn't return effects if the "now time" is way in the future
        glucose_data = self.load_report_glucose_values("timezoned_issue_report")
        carb_effects = self.load_report_carb_effects("timezoned_issue_report")
        counteraction_effects = self.load_report_counteraction_effects(
            "timezoned_issue_report"
        )
        now_time = datetime.strptime(
            "2019-07-30 17:06:59 +0000", "%Y-%m-%d %H:%M:%S %z"
        )
        (dates, values) = update_retrospective_glucose_effect(
            *glucose_data,
            *carb_effects,
            *counteraction_effects,
            recency_interval=15,
            retrospective_correction_grouping_interval=30,
            now_time=now_time
        )
        self.assertEqual(0, len(dates))


class TestLoopDataManagerDosingFromEffects(unittest.TestCase):
    INSULIN_SENSITIVITY_STARTS = [time(0, 0), time(9, 0)]
    INSULIN_SENSITIVITY_ENDS = [time(9, 0), time(23, 59)]
    INSULIN_SENSITIVITY_VALUES = [45, 55]
    SENSITIVITY = (
        INSULIN_SENSITIVITY_STARTS,
        INSULIN_SENSITIVITY_ENDS,
        INSULIN_SENSITIVITY_VALUES,
    )

    GLUCOSE_RANGE_STARTS = [time(0, 0), time(8, 0), time(21, 0)]
    GLUCOSE_RANGE_ENDS = [time(8, 0), time(21, 0), time(23, 59)]
    GLUCOSE_RANGE_MINS = [100, 90, 100]
    GLUCOSE_RANGE_MAXES = [110, 100, 110]

    BASAL_RATE_STARTS = [time(0, 0), time(15, 0)]
    BASAL_RATE_VALUES = [1, 0.85]
    BASAL_RATE_MINUTES = [0, 900]

    # This shouldn't actually get used, but is needed so it doesn't error
    CARB_RATIO_STARTS = [time(0, 0)]
    CARB_RATIO_VALUES = [10]

    UTC_OFFSET = -25200

    SETTINGS_DICT = {
        # User-editable
        "model": [360, 75],
        "suspend_threshold": 75,
        "max_basal_rate": 5,
        "max_bolus": 10,
        "retrospective_correction_enabled": True,
        # Not commonly user-edited
        "momentum_data_interval": 15,
        "default_absorption_times": [120, 180, 240],
        "dynamic_carb_absorption_enabled": True,
        "retrospective_correction_integration_interval": 30,
        "recency_interval": 15,
        "retrospective_correction_grouping_interval": 30,
        "rate_rounder": 0.05,
        "insulin_delay": 10,
        "carb_delay": 10,
    }

    STARTER_INPUT_DICT = {
        "dose_types": [],
        "dose_start_times": [],
        "dose_end_times": [],
        "dose_values": [],
        "dose_delivered_units": [],
        "carb_dates": [],
        "carb_values": [],
        "carb_absorption_times": [],
        "settings_dictionary": SETTINGS_DICT,
        "sensitivity_ratio_start_times": INSULIN_SENSITIVITY_STARTS,
        "sensitivity_ratio_end_times": INSULIN_SENSITIVITY_ENDS,
        "sensitivity_ratio_values": INSULIN_SENSITIVITY_VALUES,
        "carb_ratio_start_times": CARB_RATIO_STARTS,
        "carb_ratio_values": CARB_RATIO_VALUES,
        "basal_rate_start_times": BASAL_RATE_STARTS,
        "basal_rate_minutes": BASAL_RATE_MINUTES,
        "basal_rate_values": BASAL_RATE_VALUES,
        "target_range_start_times": GLUCOSE_RANGE_STARTS,
        "target_range_end_times": GLUCOSE_RANGE_ENDS,
        "target_range_minimum_values": GLUCOSE_RANGE_MINS,
        "target_range_maximum_values": GLUCOSE_RANGE_MAXES,
    }

    def load_effect_fixture(self, name, offset=0):
        """ Load glucose effects from json file

        Output:
        2 lists in (date, glucose_value) format
        """
        fixture = load_fixture(name, ".json")

        dates = [
            datetime.fromisoformat(dict_.get("date")) + timedelta(seconds=offset)
            for dict_ in fixture
        ]
        glucose_values = [dict_.get("amount") for dict_ in fixture]

        assert len(dates) == len(glucose_values), "expected output shape to match"

        return (dates, glucose_values)

    def load_effect_velocity_fixture(self, resource_name, offset=0):
        """ Load counteraction effects json file

        Arguments:
        resource_name -- name of file without the extension

        Output:
        3 lists in (start_date, end_date, glucose_effects) format
        """
        fixture = load_fixture(resource_name, ".json")

        start_dates = [
            datetime.fromisoformat(dict_.get("startDate")) + timedelta(seconds=offset)
            for dict_ in fixture
        ]
        end_dates = [
            datetime.fromisoformat(dict_.get("endDate")) + timedelta(seconds=offset)
            for dict_ in fixture
        ]
        glucose_effects = [dict_.get("value") for dict_ in fixture]

        assert (
            len(start_dates) == len(end_dates) == len(glucose_effects)
        ), "expected output shape to match"

        return (start_dates, end_dates, glucose_effects)

    def test_flat_and_stable(self):
        (momentum_starts, momentum_values) = self.load_effect_fixture(
            "flat_and_stable_momentum_effect", offset=self.UTC_OFFSET
        )

        (insulin_effect_starts, insulin_effect_values) = self.load_effect_fixture(
            "flat_and_stable_insulin_effect", offset=self.UTC_OFFSET
        )

        (
            counteraction_starts,
            counteraction_ends,
            counteraction_values,
        ) = self.load_effect_velocity_fixture(
            "flat_and_stable_counteraction_effect", offset=self.UTC_OFFSET
        )

        (carb_effect_starts, carb_effect_values) = self.load_effect_fixture(
            "flat_and_stable_carb_effect", offset=self.UTC_OFFSET
        )

        now = datetime.fromisoformat("2020-08-11T20:45:02") + timedelta(
            seconds=self.UTC_OFFSET
        )
        glucose_dates = [now]
        glucose_values = [123.42849966275706]

        (
            expected_predicted_glucose_dates,
            expected_predicted_glucose_values,
        ) = self.load_effect_fixture(
            "flat_and_stable_predicted_glucose", offset=self.UTC_OFFSET
        )

        starter = deepcopy(self.STARTER_INPUT_DICT)

        test_specific_input = {
            "time_to_calculate_at": now,
            "glucose_dates": glucose_dates,
            "glucose_values": glucose_values,
            "momentum_effect_dates": momentum_starts,
            "momentum_effect_values": momentum_values,
            "now_to_dia_insulin_effect_dates": insulin_effect_starts,
            "now_to_dia_insulin_effect_values": insulin_effect_values,
            "counteraction_starts": counteraction_starts,
            "counteraction_ends": counteraction_ends,
            "counteraction_values": counteraction_values,
            "carb_effect_dates": carb_effect_starts,
            "carb_effect_values": carb_effect_values,
        }
        input_dict = {**starter, **test_specific_input}

        result = update(input_dict)
        predicted_glucose_dates = result["predicted_glucose_dates"]
        predicted_glucose_values = result["predicted_glucose_values"]

        self.assertEqual(
            len(predicted_glucose_dates), len(expected_predicted_glucose_dates)
        )

        for i in range(len(predicted_glucose_dates)):
            self.assertEqual(
                predicted_glucose_dates[i], expected_predicted_glucose_dates[i]
            )
            self.assertAlmostEqual(
                predicted_glucose_values[i], expected_predicted_glucose_values[i], 1
            )

        self.assertEqual(1.4, result["recommended_temp_basal"][0])

    def test_high_and_stable(self):
        (momentum_starts, momentum_values) = self.load_effect_fixture(
            "high_and_stable_momentum_effect", offset=self.UTC_OFFSET
        )

        (insulin_effect_starts, insulin_effect_values) = self.load_effect_fixture(
            "high_and_stable_insulin_effect", offset=self.UTC_OFFSET
        )

        (
            counteraction_starts,
            counteraction_ends,
            counteraction_values,
        ) = self.load_effect_velocity_fixture(
            "high_and_stable_counteraction_effect", offset=self.UTC_OFFSET
        )

        (carb_effect_starts, carb_effect_values) = self.load_effect_fixture(
            "high_and_stable_carb_effect", offset=self.UTC_OFFSET
        )

        now = datetime.fromisoformat("2020-08-12T12:39:22") + timedelta(
            seconds=self.UTC_OFFSET
        )
        glucose_dates = [now]
        glucose_values = [200.0]

        (
            expected_predicted_glucose_dates,
            expected_predicted_glucose_values,
        ) = self.load_effect_fixture(
            "high_and_stable_predicted_glucose", offset=self.UTC_OFFSET
        )

        starter = deepcopy(self.STARTER_INPUT_DICT)

        test_specific_input = {
            "time_to_calculate_at": now,
            "glucose_dates": glucose_dates,
            "glucose_values": glucose_values,
            "momentum_effect_dates": momentum_starts,
            "momentum_effect_values": momentum_values,
            "now_to_dia_insulin_effect_dates": insulin_effect_starts,
            "now_to_dia_insulin_effect_values": insulin_effect_values,
            "counteraction_starts": counteraction_starts,
            "counteraction_ends": counteraction_ends,
            "counteraction_values": counteraction_values,
            "carb_effect_dates": carb_effect_starts,
            "carb_effect_values": carb_effect_values,
        }
        input_dict = {**starter, **test_specific_input}

        result = update(input_dict)
        predicted_glucose_dates = result["predicted_glucose_dates"]
        predicted_glucose_values = result["predicted_glucose_values"]

        self.assertEqual(
            len(predicted_glucose_dates), len(expected_predicted_glucose_dates)
        )

        for i in range(len(predicted_glucose_dates)):
            self.assertEqual(
                predicted_glucose_dates[i], expected_predicted_glucose_dates[i]
            )
            self.assertAlmostEqual(
                predicted_glucose_values[i], expected_predicted_glucose_values[i], 1
            )

        self.assertEqual(4.65, result["recommended_temp_basal"][0])

    def test_high_and_falling(self):
        (momentum_starts, momentum_values) = self.load_effect_fixture(
            "high_and_falling_momentum_effect", offset=self.UTC_OFFSET
        )

        (insulin_effect_starts, insulin_effect_values) = self.load_effect_fixture(
            "high_and_falling_insulin_effect", offset=self.UTC_OFFSET
        )

        (
            counteraction_starts,
            counteraction_ends,
            counteraction_values,
        ) = self.load_effect_velocity_fixture(
            "high_and_falling_counteraction_effect", offset=self.UTC_OFFSET
        )

        (carb_effect_starts, carb_effect_values) = self.load_effect_fixture(
            "high_and_falling_carb_effect", offset=self.UTC_OFFSET
        )

        now = datetime.fromisoformat("2020-08-11T22:59:45") + timedelta(
            seconds=self.UTC_OFFSET
        )
        glucose_dates = [now]
        glucose_values = [200.0]

        (
            expected_predicted_glucose_dates,
            expected_predicted_glucose_values,
        ) = self.load_effect_fixture(
            "high_and_falling_predicted_glucose", offset=self.UTC_OFFSET
        )

        starter = deepcopy(self.STARTER_INPUT_DICT)

        test_specific_input = {
            "time_to_calculate_at": now,
            "glucose_dates": glucose_dates,
            "glucose_values": glucose_values,
            "momentum_effect_dates": momentum_starts,
            "momentum_effect_values": momentum_values,
            "now_to_dia_insulin_effect_dates": insulin_effect_starts,
            "now_to_dia_insulin_effect_values": insulin_effect_values,
            "counteraction_starts": counteraction_starts,
            "counteraction_ends": counteraction_ends,
            "counteraction_values": counteraction_values,
            "carb_effect_dates": carb_effect_starts,
            "carb_effect_values": carb_effect_values,
        }
        input_dict = {**starter, **test_specific_input}

        result = update(input_dict)
        predicted_glucose_dates = result["predicted_glucose_dates"]
        predicted_glucose_values = result["predicted_glucose_values"]

        self.assertEqual(
            len(predicted_glucose_dates), len(expected_predicted_glucose_dates)
        )

        for i in range(len(predicted_glucose_dates)):
            self.assertEqual(
                predicted_glucose_dates[i], expected_predicted_glucose_dates[i]
            )
            self.assertAlmostEqual(
                predicted_glucose_values[i], expected_predicted_glucose_values[i], 1
            )

        self.assertEqual(0, result["recommended_temp_basal"][0])

    def test_high_and_rising_with_cob(self):
        (momentum_starts, momentum_values) = self.load_effect_fixture(
            "high_and_rising_with_cob_momentum_effect", offset=self.UTC_OFFSET
        )

        (insulin_effect_starts, insulin_effect_values) = self.load_effect_fixture(
            "high_and_rising_with_cob_insulin_effect", offset=self.UTC_OFFSET
        )

        (
            counteraction_starts,
            counteraction_ends,
            counteraction_values,
        ) = self.load_effect_velocity_fixture(
            "high_and_rising_with_cob_counteraction_effect", offset=self.UTC_OFFSET
        )

        (carb_effect_starts, carb_effect_values) = self.load_effect_fixture(
            "high_and_rising_with_cob_carb_effect", offset=self.UTC_OFFSET
        )

        now = datetime.fromisoformat("2020-08-11T21:48:17") + timedelta(
            seconds=self.UTC_OFFSET
        )
        glucose_dates = [now]
        glucose_values = [129.93174411197853]

        (
            expected_predicted_glucose_dates,
            expected_predicted_glucose_values,
        ) = self.load_effect_fixture(
            "high_and_rising_with_cob_predicted_glucose", offset=self.UTC_OFFSET
        )

        starter = deepcopy(self.STARTER_INPUT_DICT)

        test_specific_input = {
            "time_to_calculate_at": now,
            "glucose_dates": glucose_dates,
            "glucose_values": glucose_values,
            "momentum_effect_dates": momentum_starts,
            "momentum_effect_values": momentum_values,
            "now_to_dia_insulin_effect_dates": insulin_effect_starts,
            "now_to_dia_insulin_effect_values": insulin_effect_values,
            "counteraction_starts": counteraction_starts,
            "counteraction_ends": counteraction_ends,
            "counteraction_values": counteraction_values,
            "carb_effect_dates": carb_effect_starts,
            "carb_effect_values": carb_effect_values,
        }
        input_dict = {**starter, **test_specific_input}

        result = update(input_dict)
        predicted_glucose_dates = result["predicted_glucose_dates"]
        predicted_glucose_values = result["predicted_glucose_values"]

        self.assertEqual(
            len(predicted_glucose_dates), len(expected_predicted_glucose_dates)
        )

        for i in range(len(predicted_glucose_dates)):
            self.assertEqual(
                predicted_glucose_dates[i], expected_predicted_glucose_dates[i]
            )
            self.assertAlmostEqual(
                predicted_glucose_values[i], expected_predicted_glucose_values[i], 1
            )

        self.assertEqual(1.5, result["recommended_bolus"][0])

    def test_low_and_falling(self):
        (momentum_starts, momentum_values) = self.load_effect_fixture(
            "low_and_falling_momentum_effect", offset=self.UTC_OFFSET
        )

        (insulin_effect_starts, insulin_effect_values) = self.load_effect_fixture(
            "low_and_falling_insulin_effect", offset=self.UTC_OFFSET
        )

        (
            counteraction_starts,
            counteraction_ends,
            counteraction_values,
        ) = self.load_effect_velocity_fixture(
            "low_and_falling_counteraction_effect", offset=self.UTC_OFFSET
        )

        (carb_effect_starts, carb_effect_values) = self.load_effect_fixture(
            "low_and_falling_carb_effect", offset=self.UTC_OFFSET
        )

        now = datetime.fromisoformat("2020-08-11T22:06:06") + timedelta(
            seconds=self.UTC_OFFSET
        )
        glucose_dates = [now]
        glucose_values = [75.10768374646841]

        (
            expected_predicted_glucose_dates,
            expected_predicted_glucose_values,
        ) = self.load_effect_fixture(
            "low_and_falling_predicted_glucose", offset=self.UTC_OFFSET
        )

        starter = deepcopy(self.STARTER_INPUT_DICT)

        test_specific_input = {
            "time_to_calculate_at": now,
            "glucose_dates": glucose_dates,
            "glucose_values": glucose_values,
            "momentum_effect_dates": momentum_starts,
            "momentum_effect_values": momentum_values,
            "now_to_dia_insulin_effect_dates": insulin_effect_starts,
            "now_to_dia_insulin_effect_values": insulin_effect_values,
            "counteraction_starts": counteraction_starts,
            "counteraction_ends": counteraction_ends,
            "counteraction_values": counteraction_values,
            "carb_effect_dates": carb_effect_starts,
            "carb_effect_values": carb_effect_values,
        }
        input_dict = {**starter, **test_specific_input}

        result = update(input_dict)
        predicted_glucose_dates = result["predicted_glucose_dates"]
        predicted_glucose_values = result["predicted_glucose_values"]

        self.assertEqual(
            len(predicted_glucose_dates), len(expected_predicted_glucose_dates)
        )

        for i in range(len(predicted_glucose_dates)):
            self.assertEqual(
                predicted_glucose_dates[i], expected_predicted_glucose_dates[i]
            )
            self.assertAlmostEqual(
                predicted_glucose_values[i], expected_predicted_glucose_values[i], 1
            )

        self.assertEqual(0, result["recommended_temp_basal"][0])

    def test_low_with_low_treatment(self):
        (momentum_starts, momentum_values) = self.load_effect_fixture(
            "low_with_low_treatment_momentum_effect", offset=self.UTC_OFFSET
        )

        (insulin_effect_starts, insulin_effect_values) = self.load_effect_fixture(
            "low_with_low_treatment_insulin_effect", offset=self.UTC_OFFSET
        )

        (
            counteraction_starts,
            counteraction_ends,
            counteraction_values,
        ) = self.load_effect_velocity_fixture(
            "low_with_low_treatment_counteraction_effect", offset=self.UTC_OFFSET
        )

        (carb_effect_starts, carb_effect_values) = self.load_effect_fixture(
            "low_with_low_treatment_carb_effect", offset=self.UTC_OFFSET
        )

        now = datetime.fromisoformat("2020-08-11T22:23:55") + timedelta(
            seconds=self.UTC_OFFSET
        )
        glucose_dates = [now]
        glucose_values = [81.22399763523448]

        (
            expected_predicted_glucose_dates,
            expected_predicted_glucose_values,
        ) = self.load_effect_fixture(
            "low_with_low_treatment_predicted_glucose", offset=self.UTC_OFFSET
        )

        starter = deepcopy(self.STARTER_INPUT_DICT)

        test_specific_input = {
            "time_to_calculate_at": now,
            "glucose_dates": glucose_dates,
            "glucose_values": glucose_values,
            "momentum_effect_dates": momentum_starts,
            "momentum_effect_values": momentum_values,
            "now_to_dia_insulin_effect_dates": insulin_effect_starts,
            "now_to_dia_insulin_effect_values": insulin_effect_values,
            "counteraction_starts": counteraction_starts,
            "counteraction_ends": counteraction_ends,
            "counteraction_values": counteraction_values,
            "carb_effect_dates": carb_effect_starts,
            "carb_effect_values": carb_effect_values,
        }
        input_dict = {**starter, **test_specific_input}

        result = update(input_dict)
        predicted_glucose_dates = result["predicted_glucose_dates"]
        predicted_glucose_values = result["predicted_glucose_values"]

        self.assertEqual(
            len(predicted_glucose_dates), len(expected_predicted_glucose_dates)
        )

        for i in range(len(predicted_glucose_dates)):
            self.assertEqual(
                predicted_glucose_dates[i], expected_predicted_glucose_dates[i]
            )
            self.assertAlmostEqual(
                predicted_glucose_values[i], expected_predicted_glucose_values[i], 1
            )

        self.assertEqual(0, result["recommended_temp_basal"][0])


if __name__ == "__main__":
    unittest.main()
