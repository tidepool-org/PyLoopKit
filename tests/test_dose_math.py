#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 18:03:54 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/Loop/blob/
8c1dfdba38fbf6588b07cee995a8b28fcf80ef69/DoseMathTests/DoseMathTests.swift
"""
# pylint: disable=C0111, R0201, R0904, W0105
import unittest
from datetime import time, datetime, timedelta

from . import path_grabber  # pylint: disable=unused-import
from .loop_kit_tests import load_fixture
from pyloopkit.dose_math import recommended_temp_basal, recommended_bolus
from pyloopkit.dose import DoseType


class TestDoseMathFunctions(unittest.TestCase):
    """ unittest class to run DoseMath tests. """
    MAX_BASAL_RATE = 3
    MAX_BOLUS = 10
    SUSPEND_THRESHOLD = 55

    INSULIN_SENSITIVITY_STARTS = [time(0, 0)]
    INSULIN_SENSITIVITY_ENDS = [time(23, 59)]
    INSULIN_SENSITIVITY_VALUES = [60]
    SENSITIVITY = (INSULIN_SENSITIVITY_STARTS,
                   INSULIN_SENSITIVITY_ENDS,
                   INSULIN_SENSITIVITY_VALUES
                   )

    GLUCOSE_RANGE_STARTS = [time(0, 0)]
    GLUCOSE_RANGE_ENDS = [time(23, 59)]
    GLUCOSE_RANGE_MINS = [90]
    GLUCOSE_RANGE_MAXES = [120]
    TARGET_RANGE = (GLUCOSE_RANGE_STARTS,
                    GLUCOSE_RANGE_ENDS,
                    GLUCOSE_RANGE_MINS,
                    GLUCOSE_RANGE_MAXES
                    )

    MODEL = [360, 75]
    WALSH_MODEL = [4]

    def load_glucose_value_fixture(self, name):
        """ Load glucose effects from json file

        Output:
        2 lists in (date, glucose_value) format
        """
        fixture = load_fixture(
            name,
            ".json"
        )

        dates = [
            datetime.fromisoformat(dict_.get("date"))
            for dict_ in fixture
        ]
        glucose_values = [dict_.get("amount") for dict_ in fixture]

        assert len(dates) == len(glucose_values),\
            "expected output shape to match"

        return (dates, glucose_values)

    def basal_rate_schedule(self):
        """ Load basal schedule

        Output:
        3 lists in (rate_start_time, rate (in Units/insulin),
                    length_of_rate) format
        """
        fixture = load_fixture("read_selected_basal_profile", ".json")

        start_times = [
            datetime.strptime(dict_.get("start"), "%H:%M:%S").time()
            for dict_ in fixture
        ]
        rates = [dict_.get("rate") for dict_ in fixture]
        minutes = [dict_.get("minutes") for dict_ in fixture]

        assert len(start_times) == len(rates) == len(minutes),\
            "expected output shape to match"

        return (start_times, rates, minutes)

    """ Tests for recommended_temp_basal """
    def test_no_change(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_no_change_glucose"
        )
        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            None
        )

        self.assertIsNone(dose)

    def test_start_high_end_in_range(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_start_high_end_in_range"
        )
        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            None
        )

        self.assertIsNone(dose)

        # "Cancel" basal
        last_temp_basal = [
            DoseType.tempbasal,
            glucose[0][0] + timedelta(minutes=-11),
            glucose[0][0] + timedelta(minutes=19),
            0.125
            ]

        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            last_temp_basal
        )
        self.assertEqual(0, dose[0])
        self.assertEqual(0, dose[1])

    def test_start_low_end_in_range(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_start_low_end_in_range"
        )
        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            None
        )

        self.assertIsNone(dose)

        last_temp_basal = [
            DoseType.tempbasal,
            glucose[0][0] + timedelta(minutes=-11),
            glucose[0][0] + timedelta(minutes=19),
            1.225
            ]

        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            last_temp_basal
        )
        self.assertEqual(0, dose[0])
        self.assertEqual(0, dose[1])

    def test_correct_low_at_min(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_correct_low_at_min"
        )

        last_temp_basal = [
            DoseType.tempbasal,
            glucose[0][0] + timedelta(minutes=-21),
            glucose[0][0] + timedelta(minutes=9),
            0.125
            ]

        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            last_temp_basal
        )
        self.assertEqual(0, dose[0])
        self.assertEqual(0, dose[1])

        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            None
        )

        self.assertIsNone(dose)

    def test_start_high_end_low(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_start_high_end_low"
        )
        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            None
        )

        self.assertEqual(0, dose[0])
        self.assertEqual(30, dose[1])

    def test_start_low_end_high(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_start_low_end_high"
        )
        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            None
        )

        self.assertIsNone(dose)

        # "Cancel" basal
        last_temp_basal = [
            DoseType.tempbasal,
            glucose[0][0] + timedelta(minutes=-11),
            glucose[0][0] + timedelta(minutes=19),
            1.225
            ]

        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            last_temp_basal
        )
        self.assertEqual(0, dose[0])
        self.assertEqual(0, dose[1])

    def test_flat_and_high(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_flat_and_high"
        )
        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            None,
            rate_rounder=0.025
        )

        self.assertEqual(3, dose[0])
        self.assertEqual(30, dose[1])

    def test_high_and_falling(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_high_and_falling"
        )
        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            None,
            rate_rounder=0.025
        )

        self.assertEqual(1.425, dose[0])
        self.assertEqual(30, dose[1])

    def test_in_range_and_rising(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_in_range_and_rising"
        )
        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            None,
            rate_rounder=0.025
        )

        self.assertEqual(1.475, dose[0])
        self.assertEqual(30, dose[1])

    def test_high_and_rising(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_high_and_rising"
        )
        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            None,
            rate_rounder=0.025
        )

        self.assertEqual(3, dose[0])
        self.assertEqual(30, dose[1])

    def test_very_low_and_rising(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_very_low_end_in_range"
        )
        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            None,
            rate_rounder=0.025
        )

        self.assertEqual(0, dose[0])
        self.assertEqual(30, dose[1])

    def test_rise_after_dia(self):
        glucose = self.load_glucose_value_fixture(
            "far_future_high_bg_forecast"
        )
        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            None,
            rate_rounder=0.025
        )

        self.assertIsNone(dose)

    def test_no_input_glucose(self):
        glucose = ([], [])

        dose = recommended_temp_basal(
            *glucose,
            *self.TARGET_RANGE,
            datetime.now(),
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            *self.basal_rate_schedule(),
            self.MAX_BASAL_RATE,
            None,
            rate_rounder=0.025
        )

        self.assertIsNone(dose)

    """ Tests for recommended_bolus """
    def test_no_change_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_no_change_glucose"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(0, dose[0])

    def test_start_low_end_in_range_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_start_low_end_in_range"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(0, dose[0])

    def test_high_end_low_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_start_high_end_low"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(0, dose[0])

    def test_start_low_end_high_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_start_low_end_high"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(1.575, dose[0])
        self.assertEqual("predictedGlucoseBelowTarget", dose[2][0])
        self.assertEqual(60, dose[2][1])

    def test_start_below_suspend_threshold_end_high_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_start_low_end_high"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            70,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(0, dose[0])
        self.assertEqual("glucoseBelowSuspendThreshold", dose[2][0])
        self.assertEqual(60, dose[2][1])

    def test_dropping_below_range_then_rising_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_dropping_then_rising"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(1.4, dose[0])
        self.assertEqual("predictedGlucoseBelowTarget", dose[2][0])

    def test_start_low_end_high_with_pending_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_start_low_end_high"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            1,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(0.575, dose[0])

    def test_start_low_end_very_high_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_start_very_low_end_high"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(0, dose[0])

    def test_flat_and_high_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_flat_and_high"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(1.575, dose[0])

    def test_high_and_falling_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_high_and_falling"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(0.325, dose[0])

    def test_in_range_and_rising_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_in_range_and_rising"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(0.325, dose[0])

        # Less existing temp
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0.8,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(0, dose[0])

    def test_start_low_and_end_just_above_range_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "recommended_temp_start_low_end_just_above_range"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.MODEL,
            0,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(0.275, dose[0])

    def test_high_and_rising_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "recommend_temp_basal_high_and_rising"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(1.25, dose[0])

    def test_rise_after_dia_bolus(self):
        glucose = self.load_glucose_value_fixture(
            "far_future_high_bg_forecast"
        )
        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            glucose[0][0],
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0,
            self.MAX_BOLUS,
            0.025
        )

        self.assertEqual(0, dose[0])

    def test_no_input_glucose_bolus(self):
        glucose = ([], [])

        dose = recommended_bolus(
            *glucose,
            *self.TARGET_RANGE,
            datetime.now(),
            self.SUSPEND_THRESHOLD,
            *self.SENSITIVITY,
            self.WALSH_MODEL,
            0,
            self.MAX_BOLUS,
            0.025
            )
        self.assertEqual(0, dose[0])


if __name__ == '__main__':
    unittest.main()
