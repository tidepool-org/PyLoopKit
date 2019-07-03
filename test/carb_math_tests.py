#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 13:35:51 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKitTests/CarbMathTests.swift
"""
# pylint: disable=R0201, C0111, C0200, W0105
import unittest
from datetime import datetime, time

import path_grabber  # pylint: disable=unused-import
from loop_kit_tests import load_fixture
from carb_math import (map_, glucose_effects, carbs_on_board)
                       #, dynamic_carbs_on_board)


class TestCarbKitFunctions(unittest.TestCase):
    """ unittest class to run CarbKit tests."""

    INSULIN_SENSITIVITY_START_DATES = [time(0, 0)]
    INSULIN_SENSITIVITY_END_DATES = [time(23, 59)]
    INSULIN_SENSITIVITY_VALUES = [40]

    DEFAULT_ABSORPTION_TIMES = [60,
                                120,
                                240
                                ]

    def load_schedules(self):
        """ Load the carb schedule

        Output:
        2 lists in (schedule_offsets, carb_ratios) format
        """
        schedule = load_fixture("read_carb_ratios", ".json").get("schedule")
        # offset is in mins
        carb_sched_starts = [
            time.fromisoformat(dict_.get("start"))
            for dict_ in schedule
        ]
        carb_sched_ratios = [dict_.get("ratio") for dict_ in schedule]

        return (carb_sched_starts, carb_sched_ratios)

    def load_history_fixture(self, name):
        """ Load carb history from json file

        Argument:
        name -- name of file, without .json extension

        Output:
        3 lists in (carb_values, carb_start_dates, carb_absorption_times)
        format
        """
        fixture = load_fixture(name, ".json")
        return self.carb_entries_from_fixture(fixture)

    def load_carb_entry_fixture(self):
        """ Load carb entry

        Output:
        3 lists in (carb_values, carb_start_dates, carb_absorption_times)
        format
        """
        fixture = load_fixture("carb_entry_input", ".json")
        return self.carb_entries_from_fixture(fixture)

    def carb_entries_from_fixture(self, fixture):
        """ Convert fixture to carb entries

        Arguments:
        fixture -- the pre-loaded json fixture

        Output:
        3 lists in (carb_values, carb_start_dates, carb_absorption_times)
        format
        """
        carb_values = [dict_.get("amount") for dict_ in fixture]
        start_dates = [
            datetime.fromisoformat(dict_.get("start_at"))
            for dict_ in fixture
        ]
        absorption_times = [
            dict_.get("absorption_time") if dict_.get("absorption_time")
            else None for dict_ in fixture
        ]

        return (start_dates, carb_values, absorption_times)

    def load_effect_output_fixture(self):
        """ Load glucose effects from json file

        Output:
        2 lists in (date, glucose_value) format
        """
        fixture = load_fixture(
            "carb_effect_from_history_output",
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

    def load_cob_output_fixture(self, name):
        """ Load COB from json file

        Arguments:
        name -- name of file without the extension

        Output:
        2 lists in (date, cob_value) format
        """
        fixture = load_fixture(name, ".json")

        dates = [
            datetime.fromisoformat(dict_.get("date"))
            for dict_ in fixture
        ]
        cob_values = [dict_.get("amount") for dict_ in fixture]

        assert len(dates) == len(cob_values),\
            "expected output shape to match"

        return (dates, cob_values)

    def load_ice_input_fixture(self, name):
        """ Load insulin counteraction effects (ICE) from json file

        Arguments:
        name -- name of file without the extension

        Output:
        3 lists in (start_date, end_date, insulin_counteraction_value) format
        """
        fixture = load_fixture(name, ".json")

        start_dates = [
            datetime.fromisoformat(dict_.get("start_at"))
            for dict_ in fixture
        ]
        end_dates = [
            datetime.fromisoformat(dict_.get("end_at"))
            for dict_ in fixture
        ]
        ice_values = [dict_.get("velocity") for dict_ in fixture]

        assert len(start_dates) == len(end_dates) == len(ice_values),\
            "expected output shape to match"

        return (start_dates, end_dates, ice_values)

    """ Tests for map_ """
    def test_carb_effect_with_zero_entry(self):
        input_ice = self.load_ice_input_fixture("ice_35_min_input")

        carb_ratio_tuple = self.load_schedules()

        default_absorption_times = self.DEFAULT_ABSORPTION_TIMES

        carb_entry_starts = [input_ice[0][0]]
        carb_entry_quantities = [0]
        carb_entry_absorptions = [120]

        (absorptions,
         timelines,
         entries  # pylint: disable=W0612
         ) = map_(
             carb_entry_starts,
             carb_entry_quantities,
             carb_entry_absorptions,
             *input_ice,
             *carb_ratio_tuple,
             self.INSULIN_SENSITIVITY_START_DATES,
             self.INSULIN_SENSITIVITY_END_DATES,
             self.INSULIN_SENSITIVITY_VALUES,
             default_absorption_times[0] / default_absorption_times[1],
             default_absorption_times[1],
             0
             )

        self.assertEqual(len(absorptions), 1)
        self.assertEqual(absorptions[0][6], 0)

    """ Tests for glucose_effects (in carb_math) """
    def test_carb_effect_from_history(self):
        input_ = self.load_history_fixture("carb_effect_from_history_input")
        (expected_dates,
         expected_values
         ) = self.load_effect_output_fixture()

        carb_ratio_tuple = self.load_schedules()

        (effect_starts,
         effect_values
         ) = glucose_effects(
             *input_,
             *carb_ratio_tuple,
             self.INSULIN_SENSITIVITY_START_DATES,
             self.INSULIN_SENSITIVITY_END_DATES,
             self.INSULIN_SENSITIVITY_VALUES,
             180
             )

        self.assertEqual(
            len(expected_dates), len(effect_starts)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_starts[i]
            )
            self.assertAlmostEqual(
                expected_values[i], effect_values[i], 1
            )

    """ Tests for non-dynamic COB """
    def test_carbs_on_board_from_history(self):
        input_ = self.load_history_fixture("carb_effect_from_history_input")
        (expected_dates,
         expected_values
         ) = self.load_cob_output_fixture("carbs_on_board_output")

        (cob_starts,
         cob_values
         ) = carbs_on_board(
             *input_,
             default_absorption_time=180,
             delay=10,
             delta=5
             )

        self.assertEqual(
            len(expected_dates), len(cob_starts)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], cob_starts[i]
            )
            self.assertAlmostEqual(
                expected_values[i], cob_values[i], 1
            )

    def test_dynamic_absorption_none_observed(self):
        input_ice = self.load_ice_input_fixture("ice_35_min_input")

        (carb_starts,
         carb_values,
         carb_absorptions
         ) = self.load_carb_entry_fixture()

        carb_ratio_tuple = self.load_schedules()

        default_absorption_times = self.DEFAULT_ABSORPTION_TIMES

        carb_entry_starts = [carb_starts[2]]
        carb_entry_quantities = [carb_values[2]]
        carb_entry_absorptions = [carb_absorptions[2]]

        (expected_dates,
         expected_values
         ) = self.load_cob_output_fixture("ice_35_min_none_output")
        (absorptions,
         timelines,
         entries,  # pylint: disable=W0612
         ) = map_(
             carb_entry_starts,
             carb_entry_quantities,
             carb_entry_absorptions,
             *input_ice,
             *carb_ratio_tuple,
             self.INSULIN_SENSITIVITY_START_DATES,
             self.INSULIN_SENSITIVITY_END_DATES,
             self.INSULIN_SENSITIVITY_VALUES,
             default_absorption_times[1] / default_absorption_times[0],
             default_absorption_times[1],
             0
             )

        self.assertEqual(len(absorptions), 1)
        self.assertEqual(absorptions[0][6], 240)


if __name__ == '__main__':
    unittest.main()