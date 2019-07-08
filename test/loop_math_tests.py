#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 19:26:16 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKitTests/LoopMathTests.swift
"""
import unittest
from datetime import datetime

import path_grabber  # pylint: disable=unused-import
from loop_kit_tests import load_fixture
from loop_math import predict_glucose


class TestCarbKitFunctions(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
