#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:16:42 2019

@author: annaquinlan
"""
# pylint: disable=C0111, C0200, R0201, W0105, R0914, R0904
from datetime import datetime
import unittest

from . import path_grabber  # pylint: disable=unused-import
from pyloopkit.dose import DoseType
from pyloopkit.loop_data_manager import (get_pending_insulin,
                               update_retrospective_glucose_effect)
from .loop_kit_tests import load_fixture, find_root_path
from pyloopkit.pyloop_parser import (
    load_momentum_effects, get_glucose_data, load_insulin_effects,
    get_insulin_data, get_basal_schedule, get_carb_ratios,
    get_sensitivities, get_settings, get_counteractions, get_carb_data,
    get_retrospective_effects, parse_report_and_run
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

        return get_insulin_data(
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

    def load_report_insulin_effects(self, report_name):
        """ Load the expected insulin effects from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("insulin_effect"),\
            "expected issue report to contain insulin effect information"

        return load_insulin_effects(
            report.get("insulin_effect")
        )

    def load_report_counteraction_effects(self, report_name):
        """ Load the expected counteraction effects from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("insulin_counteraction_effects"),\
            "expected issue report to contain counteraction effect information"

        return get_counteractions(
            report.get("insulin_counteraction_effects")
        )

    def load_report_carb_effects(self, report_name):
        """ Load the expected carb effects from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("carb_effect"),\
            "expected issue report to contain carb effect information"

        return load_insulin_effects(
            report.get("carb_effect")
        )

    def load_report_retrospective_effects(self, report_name):
        """ Load the expected retrospective effects from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("retrospective_glucose_effect"),\
            "expected issue report to contain retrospective effect information"

        return get_retrospective_effects(
            report.get("retrospective_glucose_effect")
        )

    def load_report_predicted_glucoses(self, report_name):
        """ Load the expected retrospective effects from an issue report """
        report = load_fixture(report_name, ".json")

        assert report.get("predicted_glucose"),\
            "expected issue report to contain glucose prediction information"

        return load_insulin_effects(
            report.get("predicted_glucose")
        )

    def run_report_through_runner(self, report_name):
        """ Load the expected retrospective effects from an issue report """
        root = find_root_path(report_name, ".json")

        return parse_report_and_run(
            root + "/", report_name + ".json"
        )

    """ Integrated tests for all the effects """
    def test_loop_with_utc_issue_report(self):
        recommendation = self.run_report_through_runner(
            "utc_issue_report"
        )
        pyloop_predicted_glucoses = [
            recommendation.get("predicted_glucose_dates"),
            recommendation.get("predicted_glucose_values")
        ]
        expected_predicted_glucoses = self.load_report_predicted_glucoses(
            "utc_issue_report"
        )

        # check that the predicted glucose values are the same
        self.assertEqual(
            len(pyloop_predicted_glucoses[0]),
            len(expected_predicted_glucoses[0])
        )
        for i in range(0, len(pyloop_predicted_glucoses[0])):
            self.assertEqual(
                pyloop_predicted_glucoses[0][i],
                expected_predicted_glucoses[0][i]
            )
            self.assertAlmostEqual(
                pyloop_predicted_glucoses[1][i],
                expected_predicted_glucoses[1][i], 1
            )

        # check that the basal and bolus recommendations are as-expected
        self.assertEqual(recommendation.get("recommended_temp_basal")[0], 1.1)
        self.assertEqual(recommendation.get("recommended_temp_basal")[1], 30)
        self.assertEqual(recommendation.get("recommended_bolus")[0], 0)

    def test_loop_with_timezoned_issue_report(self):
        recommendation = self.run_report_through_runner(
            "timezoned_issue_report"
        )
        pyloop_predicted_glucoses = [
            recommendation.get("predicted_glucose_dates"),
            recommendation.get("predicted_glucose_values")
        ]
        expected_predicted_glucoses = self.load_report_predicted_glucoses(
            "timezoned_issue_report"
        )

        self.assertEqual(
            len(pyloop_predicted_glucoses[0]),
            len(expected_predicted_glucoses[0])
        )
        for i in range(0, len(pyloop_predicted_glucoses[0])):
            self.assertAlmostEqual(
                pyloop_predicted_glucoses[1][i],
                expected_predicted_glucoses[1][i], 1
            )

        # check that the basal and bolus recommendations are as-expected
        self.assertIsNone(recommendation.get("recommended_temp_basal"))
        self.assertEqual(recommendation.get("recommended_bolus")[0], 0)
        self.assertAlmostEqual(recommendation.get("recommended_bolus")[2][1],
                               68.1475, 1)

    def test_loop_with_high_glucose_issue_report(self):
        recommendation = self.run_report_through_runner(
            "high_bg_recommended_basal_and_bolus_report"
        )
        pyloop_predicted_glucoses = [
            recommendation.get("predicted_glucose_dates"),
            recommendation.get("predicted_glucose_values")
        ]
        expected_predicted_glucoses = self.load_report_predicted_glucoses(
            "high_bg_recommended_basal_and_bolus_report"
        )

        for i in range(0, len(expected_predicted_glucoses[0])):
            self.assertAlmostEqual(
                pyloop_predicted_glucoses[1][i],
                expected_predicted_glucoses[1][i], 1
            )

        self.assertEqual(recommendation.get("recommended_temp_basal")[0], 1.2)
        self.assertEqual(recommendation.get("recommended_temp_basal")[1], 30)
        self.assertEqual(recommendation.get("recommended_bolus")[0], 0.15)

    def test_loop_with_one_basal_issue_report(self):
        recommendation = self.run_report_through_runner(
            "one_basal_issue_report"
        )
        pyloop_predicted_glucoses = [
            recommendation.get("predicted_glucose_dates"),
            recommendation.get("predicted_glucose_values")
        ]
        expected_predicted_glucoses = self.load_report_predicted_glucoses(
            "one_basal_issue_report"
        )

        self.assertEqual(
            len(pyloop_predicted_glucoses[0]),
            len(expected_predicted_glucoses[0])
        )
        for i in range(0, len(pyloop_predicted_glucoses[0])):
            self.assertAlmostEqual(
                pyloop_predicted_glucoses[1][i],
                expected_predicted_glucoses[1][i], 1
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
            0.1
            ]

        pending_insulin = get_pending_insulin(
            now_time,
            *basal_schedule,
            last_temporary_basal
            )

        self.assertEqual(0, pending_insulin)

    def test_short_temp_pending_insulin(self):
        now_time = datetime.fromisoformat("2019-08-01T12:15:00")
        basal_schedule = self.load_report_basal_schedule("loop_issue_report")

        last_temporary_basal = [
            DoseType.tempbasal,
            datetime.fromisoformat("2019-08-01T12:00:00"),
            datetime.fromisoformat("2019-08-01T12:16:00"),
            1.3
            ]

        pending_insulin = get_pending_insulin(
            now_time,
            *basal_schedule,
            last_temporary_basal
            )

        self.assertAlmostEqual(pending_insulin, 0.0075, 5)

        # add a pending bolus
        pending_insulin = get_pending_insulin(
            now_time,
            *basal_schedule,
            last_temporary_basal,
            0.5
            )
        self.assertAlmostEqual(pending_insulin, 0.5075, 5)

    def test_pending_insulin_edge_cases(self):
        now_time = datetime.fromisoformat("2019-08-01T12:15:00")
        basal_schedule = self.load_report_basal_schedule("loop_issue_report")

        # when there's no temp basal
        last_temporary_basal = None
        pending_insulin = get_pending_insulin(
            now_time,
            *basal_schedule,
            last_temporary_basal
            )
        self.assertEqual(pending_insulin, 0)

        # when the temp basal has already expired
        last_temporary_basal = [
            DoseType.tempbasal,
            datetime.fromisoformat("2019-08-01T11:00:00"),
            datetime.fromisoformat("2019-08-01T11:16:00"),
            0.8
            ]
        pending_insulin = get_pending_insulin(
            now_time,
            *basal_schedule,
            last_temporary_basal
            )

        self.assertEqual(pending_insulin, 0)

        # when it isn't actually a temporary basal
        last_temporary_basal = [
            "Bolus",
            datetime.fromisoformat("2019-08-01T12:00:00"),
            datetime.fromisoformat("2019-08-01T12:30:00"),
            5.3
            ]
        pending_insulin = get_pending_insulin(
            now_time,
            *basal_schedule,
            last_temporary_basal
            )
        self.assertEqual(pending_insulin, 0)

        # when the start and end times are reversed
        last_temporary_basal = [
            DoseType.tempbasal,
            datetime.fromisoformat("2019-08-01T12:55:00"),
            datetime.fromisoformat("2019-08-01T12:40:00"),
            0.95
            ]
        pending_insulin = get_pending_insulin(
            now_time,
            *basal_schedule,
            last_temporary_basal
            )
        self.assertEqual(pending_insulin, 0)

    """ Tests for update_retrospective_glucose_effect """
    def test_retrospective_glucose_effect_only_bolus(self):
        glucose_data = self.load_report_glucose_values(
            "timezoned_issue_report"
        )
        carb_effects = self.load_report_carb_effects(
            "timezoned_issue_report"
        )
        counteraction_effects = self.load_report_counteraction_effects(
            "timezoned_issue_report"
        )
        now_time = datetime.strptime(
            "2019-07-25 22:50:57 +0000", "%Y-%m-%d %H:%M:%S %z"
        )

        (expected_dates,
         expected_values
         ) = self.load_report_retrospective_effects(
             "timezoned_issue_report"
         )

        (dates,
         values
         ) = update_retrospective_glucose_effect(
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
        glucose_data = self.load_report_glucose_values(
            "basal_and_bolus_report"
        )
        carb_effects = self.load_report_carb_effects(
            "basal_and_bolus_report"
        )
        counteraction_effects = self.load_report_counteraction_effects(
            "basal_and_bolus_report"
        )
        now_time = datetime.strptime(
            "2019-07-29 17:06:59 +0000", "%Y-%m-%d %H:%M:%S %z"
        )

        (expected_dates,
         expected_values
         ) = self.load_report_retrospective_effects(
             "basal_and_bolus_report"
         )

        (dates,
         values
         ) = update_retrospective_glucose_effect(
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
        glucose_data = self.load_report_glucose_values(
            "basal_and_bolus_report"
        )
        carb_effects = self.load_report_carb_effects(
            "basal_and_bolus_report"
        )
        counteraction_effects = ([], [], [])
        now_time = datetime.strptime(
            "2019-07-29 17:06:59 +0000", "%Y-%m-%d %H:%M:%S %z"
        )
        (dates,
         values
         ) = update_retrospective_glucose_effect(
             *glucose_data,
             *carb_effects,
             *counteraction_effects,
             recency_interval=15,
             retrospective_correction_grouping_interval=30,
             now_time=now_time
             )

        self.assertEqual(0, len(dates))

        # it shouldn't return effects if the "now time" is way in the future
        glucose_data = self.load_report_glucose_values(
            "timezoned_issue_report"
        )
        carb_effects = self.load_report_carb_effects(
            "timezoned_issue_report"
        )
        counteraction_effects = self.load_report_counteraction_effects(
            "timezoned_issue_report"
        )
        now_time = datetime.strptime(
            "2019-07-30 17:06:59 +0000", "%Y-%m-%d %H:%M:%S %z"
        )
        (dates,
         values
         ) = update_retrospective_glucose_effect(
             *glucose_data,
             *carb_effects,
             *counteraction_effects,
             recency_interval=15,
             retrospective_correction_grouping_interval=30,
             now_time=now_time
             )
        self.assertEqual(0, len(dates))


if __name__ == '__main__':
    unittest.main()
