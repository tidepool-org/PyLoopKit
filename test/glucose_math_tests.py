#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKitTests/GlucoseMathTests.swift
"""
import unittest
import path_grabber # pylint: disable=unused-import
from datetime import datetime
from loop_kit_tests import load_fixture
from glucose_effect import GlucoseEffect
from glucose_effect_velocity import GlucoseEffectVelocity
from glucose_math import linear_momentum_effect


class GlucoseFixtureValue:
    """ Constructs a glucose value for the purposes of running tests.

    Attributes:
    start_date -- date and time of glucose value
    quantity -- glucose value (mg/dL)
    is_display_only -- whether to do computations with
    provenance_identifier -- where value came from; defaults to
                                 com.loopkit.LoopKitTests
    """
    def __init__(self, start_date, quantity, is_display_only,
                 provenance_identifier):
        self.start_date = start_date
        self.quantity = quantity
        self.is_display_only = is_display_only
        self.provenance_identifier = (provenance_identifier
                                      or "com.loopkit.LoopKitTests")

    def __lt__(self, other):
        return self.start_date < other.start_date

    def __eq__(self, other):
        return (self.start_date == other.start_date and
                self.quantity == other.quantity and
                self.is_display_only == other.is_display_only and
                self.provenance_identifier == other.provenance_identifier)


class TestGlucoseKitFunctions(unittest.TestCase):
    """ unittest class to run GlucoseKit tests."""

    def load_input_fixture(self, resource_name):
        """ Load input json file

        Keyword arguments:
        resource_name -- name of file without the extension

        Output:
        list of GlucoseFixtureValue
        """
        fixture = load_fixture(resource_name, ".json")

        def glucose_fixture_maker(dict_):
            return GlucoseFixtureValue(
                datetime.fromisoformat(dict_.get("date")),
                dict_.get("amount"),
                dict_.get("display_only") or False,
                dict_.get("provenance_identifier"))
        return list(map(glucose_fixture_maker, fixture))

    def load_output_fixture(self, resource_name):
        """ Load output json file

        Keyword arguments:
        resource_name -- name of file without the extension

        Output:
        list of GlucoseEffect
        """
        fixture = load_fixture(resource_name, ".json")

        def glucose_effect_maker(dict_):
            return GlucoseEffect(
                datetime.fromisoformat(dict_.get("date")),
                dict_.get("amount"))

        return list(map(glucose_effect_maker, fixture))

    def load_effect_velocity_fixture(self, resource_name):
        """ Load effect-velocity json file

        Keyword arguments:
        resource_name -- name of file without the extension

        Output:
        list of GlucoseEffectVelocity
        """
        fixture = load_fixture(resource_name, ".json")

        def glucose_effect_velocity_maker(dict_):
            return GlucoseEffectVelocity(
                datetime.fromisoformat(dict_.get("start_date")),
                datetime.fromisoformat(dict_.get("end_date")),
                dict_.get("value"))

        return list(map(glucose_effect_velocity_maker, fixture))

    """ Tests for linear_momentum_effect """
    def test_momentum_effect_for_bouncing_glucose(self):
        input_ = self.load_input_fixture("momentum_effect_bouncing_glucose" +
                                         "_input")
        output = self.load_output_fixture("momentum_effect_bouncing_glucose" +
                                          "_output")

        effects = linear_momentum_effect(input_)

        self.assertEqual(len(output), len(effects))
        for(expected, calculated) in zip(output, effects):
            self.assertEqual(expected.start_date, calculated.start_date)
            self.assertAlmostEqual(expected.quantity,
                                   calculated.quantity, 2)

    def test_momentum_effect_for_rising_glucose(self):
        input_ = self.load_input_fixture("momentum_effect_rising_glucose" +
                                         "_input")
        output = self.load_output_fixture("momentum_effect_rising_glucose" +
                                          "_output")

        effects = linear_momentum_effect(input_)

        self.assertEqual(len(output), len(effects))
        for(expected, calculated) in zip(output, effects):
            self.assertEqual(expected.start_date, calculated.start_date)
            self.assertAlmostEqual(expected.quantity,
                                   calculated.quantity, 2)

    def test_momentum_effect_for_rising_glucose_doubles(self):
        input_ = self.load_input_fixture("momentum_effect_rising_glucose" +
                                         "_double_entries_input")
        output = self.load_output_fixture("momentum_effect_rising_glucose" +
                                          "_output")

        effects = linear_momentum_effect(input_)

        self.assertEqual(len(output), len(effects))
        for(expected, calculated) in zip(output, effects):
            self.assertEqual(expected.start_date, calculated.start_date)
            self.assertAlmostEqual(expected.quantity,
                                   calculated.quantity, 2)


if __name__ == '__main__':
    unittest.main()
