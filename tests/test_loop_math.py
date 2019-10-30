#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 19:26:16 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKitTests/LoopMathTests.swift
"""
# pylint: disable=C0111, C0200, R0201, W0105
import unittest
from datetime import datetime

from . import path_grabber  # pylint: disable=unused-import
from .loop_kit_tests import load_fixture
from pyloopkit.loop_math import predict_glucose, decay_effect, subtracting, combined_sums
from pyloopkit.date import time_interval_since


class TestLoopMathFunctions(unittest.TestCase):
    """ unittest class to run LoopMath tests. """

    def load_glucose_effect_fixture_iso_time(self, name):
        """ Load glucose effects from json file if dates are in ISO format

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

    def load_counteraction_input_fixture(self, name):
        """ Load insulin counteraction effects from json file

        Arguments:
        name -- name of file without the extension

        Output:
        3 lists in (start_date, end_date, insulin_counteraction_value) format
        """
        fixture = load_fixture(name, ".json")

        start_dates = [
            datetime.fromisoformat(dict_.get("startDate"))
            if "T" in dict_.get("startDate")
            else datetime.strptime(
                dict_.get("startDate"),
                "%Y-%m-%d %H:%M:%S %z"
            )
            for dict_ in fixture
        ]
        end_dates = [
            datetime.fromisoformat(dict_.get("endDate"))
            if "T" in dict_.get("endDate")
            else datetime.strptime(
                dict_.get("endDate"),
                "%Y-%m-%d %H:%M:%S %z"
            )
            for dict_ in fixture
        ]
        ice_values = [dict_.get("value") for dict_ in fixture]

        assert len(start_dates) == len(end_dates) == len(ice_values),\
            "expected output shape to match"

        return (start_dates, end_dates, ice_values)

    def load_glucose_effect_fixture_normal_time(self, name):
        """ Load glucose effects from json file if dates are in format
            "%Y-%m-%d %H:%M:%S %z"

        Output:
        2 lists in (date, glucose_value) format
        """
        fixture = load_fixture(
            name,
            ".json"
        )

        dates = [
            datetime.strptime(
                dict_.get("date"),
                "%Y-%m-%d %H:%M:%S %z"
            )
            for dict_ in fixture
        ]
        glucose_values = [dict_.get("value") for dict_ in fixture]

        assert len(dates) == len(glucose_values),\
            "expected output shape to match"

        return (dates, glucose_values)

    def load_sample_value_fixture(self, name):
        """ Load sample values from json file

        Output:
        2 lists in (date, glucose_value) format
        """
        fixture = load_fixture(
            name,
            ".json"
        )

        dates = [
            datetime.strptime(
                dict_.get("startDate"),
                "%Y-%m-%dT%H:%M:%S%z"
            )
            for dict_ in fixture
        ]
        glucose_values = [dict_.get("value") for dict_ in fixture]

        assert len(dates) == len(glucose_values),\
            "expected output shape to match"

        return (dates, glucose_values)

    def load_glucose_history_fixture(self, name):
        """ Load glucose history values from json file

        Output:
        2 lists in (date, glucose_value) format
        """
        fixture = load_fixture(
            name,
            ".json"
        )

        dates = [
            datetime.fromisoformat(dict_.get("display_time"))
            for dict_ in fixture
        ]
        glucose_values = [dict_.get("glucose") for dict_ in fixture]

        assert len(dates) == len(glucose_values),\
            "expected output shape to match"

        return (dates, glucose_values)

    def load_glucose_value_fixture(self, name):
        """ Load sample values from json file

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

    def carb_effect(self):
        return self.load_glucose_effect_fixture_iso_time(
            "glucose_from_effects_carb_effect_input"
        )

    def insulin_effect(self):
        return self.load_glucose_effect_fixture_iso_time(
            "glucose_from_effects_insulin_effect_input"
        )

    """ Predict_glucose tests """
    def test_predict_glucose_no_momentum(self):
        glucose = self.load_glucose_history_fixture(
            "glucose_from_effects_glucose_input"
        )
        (expected_dates,
         expected_values
         ) = self.load_glucose_value_fixture(
             "glucose_from_effects_no_momentum_output"
             )

        (predicted_dates,
         predicted_values
         ) = predict_glucose(
             glucose[0][0], glucose[1][0],
             [], [],
             *self.carb_effect(),
             *self.insulin_effect()
             )
        self.assertEqual(
            len(expected_dates), len(predicted_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], predicted_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], predicted_values[i], 3
            )

    def test_predict_glucose_flat_momentum(self):
        glucose = self.load_glucose_history_fixture(
            "glucose_from_effects_momentum_flat_glucose_input"
        )
        momentum = self.load_glucose_effect_fixture_iso_time(
            "glucose_from_effects_momentum_flat_input"
        )
        (expected_dates,
         expected_values
         ) = self.load_glucose_value_fixture(
             "glucose_from_effects_momentum_flat_output"
             )

        (predicted_dates,
         predicted_values
         ) = predict_glucose(
             glucose[0][0], glucose[1][0],
             *momentum,
             *self.carb_effect(),
             *self.insulin_effect()
             )
        self.assertEqual(
            len(expected_dates), len(predicted_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], predicted_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], predicted_values[i], 3
            )

    def test_predict_glucose_up_momentum(self):
        glucose = self.load_glucose_history_fixture(
            "glucose_from_effects_glucose_input"
        )
        momentum = self.load_glucose_effect_fixture_iso_time(
            "glucose_from_effects_momentum_up_input"
        )
        (expected_dates,
         expected_values
         ) = self.load_glucose_value_fixture(
             "glucose_from_effects_momentum_up_output"
             )

        (predicted_dates,
         predicted_values
         ) = predict_glucose(
             glucose[0][0], glucose[1][0],
             *momentum,
             *self.carb_effect(),
             *self.insulin_effect()
             )
        self.assertEqual(
            len(expected_dates), len(predicted_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], predicted_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], predicted_values[i], 3
            )

    def test_predict_glucose_down_momentum(self):
        glucose = self.load_glucose_history_fixture(
            "glucose_from_effects_glucose_input"
        )
        momentum = self.load_glucose_effect_fixture_iso_time(
            "glucose_from_effects_momentum_down_input"
        )
        (expected_dates,
         expected_values
         ) = self.load_glucose_value_fixture(
             "glucose_from_effects_momentum_down_output"
             )

        (predicted_dates,
         predicted_values
         ) = predict_glucose(
             glucose[0][0], glucose[1][0],
             *momentum,
             *self.carb_effect(),
             *self.insulin_effect()
             )
        self.assertEqual(
            len(expected_dates), len(predicted_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], predicted_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], predicted_values[i], 3
            )

    def test_predict_glucose_blend_momentum(self):
        glucose = self.load_glucose_history_fixture(
            "glucose_from_effects_momentum_blend_glucose_input"
        )
        momentum = self.load_glucose_effect_fixture_iso_time(
            "glucose_from_effects_momentum_blend_momentum_input"
        )
        insulin_effect = self.load_glucose_effect_fixture_iso_time(
            "glucose_from_effects_momentum_blend_insulin_effect_input"
        )
        (expected_dates,
         expected_values
         ) = self.load_glucose_value_fixture(
             "glucose_from_effects_momentum_blend_output"
             )

        (predicted_dates,
         predicted_values
         ) = predict_glucose(
             glucose[0][0], glucose[1][0],
             *momentum,
             *self.carb_effect(),
             *insulin_effect
             )
        self.assertEqual(
            len(expected_dates), len(predicted_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], predicted_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], predicted_values[i], 3
            )

    def test_predict_glucose_starting_effects_non_zero(self):
        glucose = self.load_sample_value_fixture(
            "glucose_from_effects_non_zero_glucose_input"
        )
        insulin_effect = self.load_sample_value_fixture(
            "glucose_from_effects_non_zero_insulin_input"
        )
        carb_effect = self.load_sample_value_fixture(
            "glucose_from_effects_non_zero_carb_input"
        )
        (expected_dates,
         expected_values
         ) = self.load_sample_value_fixture(
             "glucose_from_effects_non_zero_output"
             )

        (predicted_dates,
         predicted_values
         ) = predict_glucose(
             glucose[0][0], glucose[1][0],
             [], [],
             *carb_effect,
             *insulin_effect
             )
        self.assertEqual(
            len(expected_dates), len(predicted_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], predicted_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], predicted_values[i], 3
            )

    """ Decay_effects tests """
    def test_decay_effect(self):
        glucose_date = datetime(2016, 2, 1, 10, 13, 20)
        glucose_value = 100
        starting_effect = 2

        (dates,
         values
         ) = decay_effect(
             glucose_date, glucose_value,
             starting_effect,
             30
             )

        self.assertEqual(
            [100, 110, 118, 124, 128, 130, 130],
            values
        )

        start_date = dates[0]
        time_deltas = []

        for time in dates:
            time_deltas.append(
                time_interval_since(time, start_date) / 60
            )

        self.assertEqual(
            [0, 5, 10, 15, 20, 25, 30],
            time_deltas
        )

        (dates,
         values
         ) = decay_effect(
             glucose_date, glucose_value,
             -0.5,
             30
             )
        self.assertEqual(
            [100, 97.5, 95.5, 94, 93, 92.5, 92.5],
            values
        )

    def test_decay_effect_with_even_glucose(self):
        glucose_date = datetime(2016, 2, 1, 10, 15, 0)
        glucose_value = 100
        starting_effect = 2

        (dates,
         values
         ) = decay_effect(
             glucose_date, glucose_value,
             starting_effect,
             30
             )

        self.assertEqual(
            [100, 110, 118, 124, 128, 130],
            values
        )

        start_date = dates[0]
        time_deltas = []

        for time in dates:
            time_deltas.append(
                time_interval_since(time, start_date) / 60
            )

        self.assertEqual(
            [0, 5, 10, 15, 20, 25],
            time_deltas
        )

        (dates,
         values
         ) = decay_effect(
             glucose_date, glucose_value,
             -0.5,
             30
             )
        self.assertEqual(
            [100, 97.5, 95.5, 94, 93, 92.5],
            values
        )

    """ Subtracting effects tests """
    def test_subtracting_carb_effect_from_ice_with_gaps(self):
        insulin_counteraction_effects = self.load_counteraction_input_fixture(
            "subtracting_carb_effect_counteration_input"
        )

        (carb_effect_starts,
         carb_effect_values
         ) = self.load_glucose_value_fixture(
             "subtracting_carb_effect_carb_input"
             )

        (expected_starts,
         expected_values
         ) = self.load_glucose_effect_fixture_normal_time(
             "ice_minus_carb_effect_with_gaps_output"
             )

        (starts,
         values
         ) = subtracting(
             *insulin_counteraction_effects,
             carb_effect_starts, [], carb_effect_values,
             5
             )

        self.assertEqual(
            len(expected_starts),
            len(starts)
        )

        for i in range(0, len(expected_starts)):
            self.assertAlmostEqual(
                expected_values[i], values[i], 2
            )

    def test_subtracting_flat_carb_effect_from_ice(self):
        insulin_counteraction_effects = self.load_counteraction_input_fixture(
            "subtracting_flat_carb_from_ice_counteraction_input"
        )

        (carb_effect_starts,
         carb_effect_values
         ) = (
             [datetime.strptime(
                 "2018-08-26 00:45:00+0000",
                 "%Y-%m-%d %H:%M:%S%z"
                 )],
             [385.8235294117647]
             )

        (expected_starts,
         expected_values
         ) = self.load_glucose_effect_fixture_normal_time(
             "ice_minus_flat_carb_effect_output"
             )

        (starts,
         values
         ) = subtracting(
             *insulin_counteraction_effects,
             carb_effect_starts, [], carb_effect_values,
             5
             )

        self.assertEqual(
            len(expected_starts),
            len(starts)
        )

        for i in range(0, len(expected_starts)):
            self.assertAlmostEqual(
                expected_values[i], values[i], 2
            )

    """ Tests for combined_sums """
    def test_combined_sums_with_gaps(self):
        (input_starts,
         input_values
         ) = self.load_glucose_effect_fixture_normal_time(
            "ice_minus_carb_effect_with_gaps_output"
        )

        (expected_starts,
         expected_ends,
         expected_values
         ) = self.load_counteraction_input_fixture(
             "combined_sums_with_gaps_output"
             )

        (starts,
         ends,
         values
         ) = combined_sums(
             input_starts, [], input_values,
             30
             )

        self.assertEqual(
            len(expected_starts),
            len(starts)
        )

        for i in range(0, len(expected_starts)):
            self.assertEqual(
                expected_starts[i], starts[i]
            )
            self.assertEqual(
                expected_ends[i], ends[i]
            )
            self.assertAlmostEqual(
                expected_values[i], values[i], 2
            )


if __name__ == '__main__':
    unittest.main()
