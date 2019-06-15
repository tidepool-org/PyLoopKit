#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKitTests/GlucoseMathTests.swift
"""

from LoopKitTests import load_fixture, date_formatter, HKQuantity
from GlucoseEffect import GlucoseEffect
from GlucoseEffectVelocity import GlucoseEffectVelocity
from GlucoseMath import linear_momentum_effect


class GlucoseFixtureValue:

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


def runTestCases():

    def load_input_fixture(resource_name):
        fixture = load_fixture(resource_name, ".json")

        def glucose_fixture_maker(dict):
            return GlucoseFixtureValue(date_formatter(dict.get("date")),
                                       HKQuantity(dict.get("unit"),
                                                  dict.get("amount")),
                                       dict.get("display_only") or False,
                                       dict.get("provenance_identifier"))
        return list(map(glucose_fixture_maker, fixture))

    def load_output_fixture(resource_name):
        fixture = load_fixture(resource_name, ".json")

        def glucose_effect_maker(dict):
            return GlucoseEffect(date_formatter(dict.get("date")),
                                 HKQuantity(dict.get("unit"),
                                            dict.get("amount")))

        return list(map(glucose_effect_maker, fixture))

    def load_effect_velocity_fixture(resource_name):
        fixture = load_fixture(resource_name, ".json")

        def glucose_effect_velocity_maker(dict):
            return GlucoseEffectVelocity(date_formatter(dict.get(
                                                        "start_date")),
                                         date_formatter(dict.get("end_date")),
                                         HKQuantity(dict.get("unit"),
                                                    dict.get("value")))

        return list(map(glucose_effect_velocity_maker, fixture))

    def test_momentum_effect_for_bouncing_glucose():
        input_ = load_input_fixture("momentum_effect_bouncing_glucose_input")
        output = load_output_fixture("momentum_effect_bouncing_glucose_output")

        effects = linear_momentum_effect(input_)

        if len(output) != len(effects):
            print("Test failed, expected output is length", len(output),
                  "but output from program is", len(effects))
        for(expected, calculated) in zip(output, effects):
            if expected.start_date != calculated.start_date:
                print("Test failed because", expected.start_date, "!=",
                      calculated.start_date)
            elif (expected.quantity.double_value
                    != calculated.quantity.double_value):
                print("Test failed because", expected.quantity.double_value,
                      "!=", calculated.quantity.double_value)
            else:
                print("Test passed!!!")

    test_momentum_effect_for_bouncing_glucose()


runTestCases()
