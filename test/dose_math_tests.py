#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 18:03:54 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/Loop/blob/
8c1dfdba38fbf6588b07cee995a8b28fcf80ef69/DoseMathTests/DoseMathTests.swift
"""
import unittest
from datetime import time, datetime

import path_grabber  # pylint: disable=unused-import
from loop_kit_tests import load_fixture
from dose_math import recommended_temp_basal


class TestDoseMathFunctions(unittest.TestCase):
    """ unittest class to run DoseMath tests. """
    MAX_BASAL_RATE = 3
    SUSPEND_THRESHOLD = 55

    INSULIN_SENSITIVITY_STARTS = [time(0, 0)]
    INSULIN_SENSITIVITY_ENDS = [time(23, 59)]
    INSULIN_SENSITIVITY_VALUES = [40]
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


if __name__ == '__main__':
    unittest.main()