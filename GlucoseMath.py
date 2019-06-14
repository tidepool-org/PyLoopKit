#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 09:53:33 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKit/GlucoseKit/GlucoseMath.swift
"""

def 

"""
func linearMomentumEffect(
        duration: TimeInterval = TimeInterval(minutes: 30),
        delta: TimeInterval = TimeInterval(minutes: 5)
    ) -> [GlucoseEffect] {
        guard
            self.count > 2,  // Linear regression isn't much use without 3 or more entries.
            isContinuous() && isCalibrated && hasSingleProvenance,
            let firstSample = self.first,
            let lastSample = self.last,
            let (startDate, endDate) = LoopMath.simulationDateRangeForSamples([lastSample], duration: duration, delta: delta)
        else {
            return []
        }

        /// Choose a unit to use during raw value calculation
        let unit = HKUnit.milligramsPerDeciliter

        let (slope: slope, intercept: _) = self.map { (
            x: $0.startDate.timeIntervalSince(firstSample.startDate),
            y: $0.quantity.doubleValue(for: unit)
        ) }.linearRegression()

        guard slope.isFinite else {
            return []
        }

        var date = startDate
        var values = [GlucoseEffect]()

        repeat {
            let value = Swift.max(0, date.timeIntervalSince(lastSample.startDate)) * slope

            values.append(GlucoseEffect(startDate: date, quantity: HKQuantity(unit: unit, doubleValue: value)))
            date = date.addingTimeInterval(delta)
        } while date <= endDate

        return values
    }
"""

# object list contains GlucoseFixtureValue objects
def linear_momentum_effect(object_list, duration, delta):
    if (len(object_list) <= 2 or not is_continuous(object_list)
            or not is_calibrated(object_list)
            or not has_single_provenance(object_list)):
        return []
    first_sample = object_list[0]
    last_sample = object_list[len(object_list)-1]
    # STOPPED HERE TO GO WORK ON CALIBRATION/SINGLE PROV
    (start_date, end_date) = simulation_date_range_for_samples ()
    
    def create_tuples(object_):
        return
    (slope, intercept) = map()
