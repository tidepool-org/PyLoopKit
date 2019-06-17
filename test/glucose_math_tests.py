#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKitTests/GlucoseMathTests.swift
"""
import unittest
from datetime import datetime
from loop_kit_tests import load_fixture, HKQuantity
from glucose_effect import GlucoseEffect
from glucose_effect_velocity import GlucoseEffectVelocity
from glucose_math import linear_momentum_effect


class GlucoseFixtureValue:
    """ Constructs a glucose value with the following properties:
            start_date = date and time of glucose value
            quantity = HKValue with quantity and unit
            is_display_only = whether to do computations with
            provenance_identifier = where value came from; defaults to
                                    com.loopkit.LoopKitTests """
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

    def load_input_fixture(self, resource_name):
        fixture = load_fixture(resource_name, ".json")

        def glucose_fixture_maker(dict):
            return GlucoseFixtureValue(datetime.
                                       fromisoformat(dict.get("date")),
                                       HKQuantity(dict.get("unit"),
                                                  dict.get("amount")),
                                       dict.get("display_only") or False,
                                       dict.get("provenance_identifier"))
        self.input = list(map(glucose_fixture_maker, fixture))

    def load_output_fixture(self, resource_name):
        fixture = load_fixture(resource_name, ".json")

        def glucose_effect_maker(dict):
            return GlucoseEffect(datetime.fromisoformat(dict.get("date")),
                                 HKQuantity(dict.get("unit"),
                                            dict.get("amount")))

        self.output = list(map(glucose_effect_maker, fixture))

    def load_effect_velocity_fixture(self, resource_name):
        fixture = load_fixture(resource_name, ".json")

        def glucose_effect_velocity_maker(dict):
            return GlucoseEffectVelocity(datetime.fromisoformat(dict.get(
                "start_date")),
                                         datetime.fromisoformat(dict.get(
                                                 "end_date")),
                                         HKQuantity(dict.get("unit"),
                                                    dict.get("value")))

        self.output = list(map(glucose_effect_velocity_maker, fixture))

    def test_momentum_effect_for_bouncing_glucose(self):
        self.load_input_fixture("momentum_effect_bouncing_glucose_input")
        self.load_output_fixture("momentum_effect_bouncing_glucose_output")

        effects = linear_momentum_effect(self.input)
        output = self.output

        self.assertEqual(len(output), len(effects))
        for(expected, calculated) in zip(output, effects):
            self.assertEqual(expected.start_date, calculated.start_date)
            self.assertAlmostEqual(expected.quantity.double_value,
                                   calculated.quantity.double_value, 2)

    def test_momentum_effect_for_rising_glucose(self):
        self.load_input_fixture("momentum_effect_rising_glucose_input")
        self.load_output_fixture("momentum_effect_rising_glucose_output")

        effects = linear_momentum_effect(self.input)
        output = self.output

        self.assertEqual(len(output), len(effects))
        for(expected, calculated) in zip(output, effects):
            self.assertEqual(expected.start_date, calculated.start_date)
            self.assertAlmostEqual(expected.quantity.double_value,
                                   calculated.quantity.double_value, 2)

    def test_momentum_effect_for_rising_glucose_doubles(self):
        self.load_input_fixture("momentum_effect_rising_glucose" +
                                "_double_entries_input")
        self.load_output_fixture("momentum_effect_rising_glucose_output")

        effects = linear_momentum_effect(self.input)
        output = self.output

        self.assertEqual(len(output), len(effects))
        for(expected, calculated) in zip(output, effects):
            self.assertEqual(expected.start_date, calculated.start_date)
            self.assertAlmostEqual(expected.quantity.double_value,
                                   calculated.quantity.double_value, 2)


if __name__ == '__main__':
    unittest.main()
