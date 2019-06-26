#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 09:00:27 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKitTests/InsulinMathTests.swift
"""
# pylint: disable = R0201, C0111, W0105, W0612, C0200, R0914, R0904
# diable pylint warnings for "method could be function", String statement
# has no effect, unused variable (for tuple unpacking), enumerate instead
# of range
import unittest
from datetime import datetime, time
import path_grabber  # pylint: disable=unused-import
from loop_kit_tests import load_fixture
from insulin_math import dose_entries, is_continuous, insulin_on_board,\
                         glucose_effects
from exponential_insulin_model import percent_effect_remaining


class TestInsulinKitFunctions(unittest.TestCase):
    """ unittest class to run InsulinKit tests."""
    WITHIN = 30

    MODEL = [360, 75]
    WALSH_MODEL = [4]

    INSULIN_SENSITIVITY_START_DATES = [time(0, 0)]
    INSULIN_SENSITIVITY_END_DATES = [time(23, 59)]
    INSULIN_SENSITIVITY_VALUES = [40]

    def load_reservoir_fixture(self, resource_name):
        """ Load reservior data from json file

        Arguments:
        resource_name -- name of file without the extension

        Variable names:
        fixture -- list of dictionaries; each dictionary contains properties
        of a NewReserviorValue

        Output:
        2 lists in (date, units_given) format
        """
        fixture = load_fixture(resource_name, ".json")

        dates = [datetime.fromisoformat(dict_.get("date"))
                 for dict_ in fixture]
        unit_volumes = [dict_.get("amount") for dict_ in fixture]

        assert len(dates) == len(unit_volumes),\
            "expected output shape to match"

        return (dates, unit_volumes)

    def load_dose_fixture(self, resource_name):
        """ Load dose from json file

        Arguments:
        resource_name -- name of file without the extension

        Output:
        5 lists in (dose_type (basal/bolus), start_dates, end_dates,
                    values (in units/insulin), scheduled_basal_rates) format
        """
        fixture = load_fixture(resource_name, ".json")

        dose_types = [dict_.get("type") or "!" for dict_ in fixture]
        start_dates = [datetime.fromisoformat(dict_.get("start_at"))
                       for dict_ in fixture]
        end_dates = [datetime.fromisoformat(dict_.get("end_at"))
                     for dict_ in fixture]
        values = [dict_.get("amount") for dict_ in fixture]
        # not including description, unit, and raw bc not relevent
        scheduled_basal_rates = [dict_.get("scheduled") or 0
                                 for dict_ in fixture]

        assert len(dose_types) == len(start_dates) == len(end_dates) ==\
            len(values) == len(scheduled_basal_rates),\
            "expected output shape to match"
        # if dose_type doesn't exist (meaning there's an "!"), remove entry
        if "!" in dose_types:
            for i in range(0, len(dose_types)):
                if dose_types[i] == "!":
                    del dose_types[i]
                    del start_dates[i]
                    del end_dates[i]
                    del values[i]
                    del scheduled_basal_rates[i]

        return (dose_types, start_dates, end_dates, values,
                scheduled_basal_rates)

    def load_insulin_value_fixture(self, resource_name):
        """ Load insulin values from json file

        Arguments:
        resource_name -- name of file without the extension

        Output:
        2 lists in (start_date, insulin_amount) format
        """
        fixture = load_fixture(resource_name, ".json")

        start_dates = [datetime.fromisoformat(dict_.get("date"))
                       for dict_ in fixture]
        insulin_values = [dict_.get("value") for dict_ in fixture]

        assert len(start_dates) == len(insulin_values),\
            "expected output shape to match"

        return (start_dates, insulin_values)

    def load_glucose_effect_fixture(self, resource_name):
        """ Load glucose effects from json file

        Arguments:
        resource_name -- name of file without the extension

        Output:
        2 lists in (date, glucose_value) format
        """
        fixture = load_fixture(resource_name, ".json")

        dates = [datetime.fromisoformat(dict_.get("date"))
                 for dict_ in fixture]
        glucose_values = [dict_.get("amount") for dict_ in fixture]

        assert len(dates) == len(glucose_values),\
            "expected output shape to match"

        return (dates, glucose_values)

    def load_basal_rate_schedule_fixture(self, resource_name):
        """ Load basal schedule from json file

        Arguments:
        resource_name -- name of file without the extension

        Output:
        3 lists in (rate_start_time, rate (in units/insulin),
                    length_of_rate) format
        """
        fixture = load_fixture(resource_name, ".json")

        start_times = [datetime.strptime(dict_.get("start"), "%H:%M:%S").time()
                       for dict_ in fixture]
        rates = [dict_.get("rate") for dict_ in fixture]
        minutes = [dict_.get("minutes") for dict_ in fixture]

        assert len(start_times) == len(rates) == len(minutes),\
            "expected output shape to match"

        return (start_times, rates, minutes)

    """ Tests for dose_entries """
    def test_dose_entries_from_reservoir_values(self):
        (i_dates, i_volumes) = self.load_reservoir_fixture(
            "reservoir_history_with_rewind_and_prime_input")
        (out_dose_types, out_start_dates, out_end_dates, out_values,
         out_scheduled_basal_rates) = self.load_dose_fixture(
             "reservoir_history_with_rewind_and_prime_output")

        out_start_dates.reverse()
        out_end_dates.reverse()
        out_values.reverse()

        (dose_types, start_dates, end_dates, values) = dose_entries(
            i_dates, i_volumes)

        self.assertEqual(len(out_start_dates), len(start_dates))
        for i in range(0, len(out_start_dates)):
            self.assertEqual(out_start_dates[i], start_dates[i])
            self.assertEqual(out_end_dates[i], end_dates[i])
            self.assertAlmostEqual(out_values[i], values[i], 2)

    """ Tests for is_continuous """
    def test_continuous_reservoir_values(self):
        (i_dates, i_volumes) = self.load_reservoir_fixture(
            "reservoir_history_with_rewind_and_prime_input")
        self.assertTrue(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T16:40:00"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))

        # We don't assert whether it's "stale".
        self.assertTrue(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T16:40:00"),
            datetime.fromisoformat("2016-01-30T22:40:00"), self.WITHIN))
        self.assertTrue(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T16:40:00"),
            datetime.now(), self.WITHIN))

        # The values must extend the startDate boundary
        self.assertFalse(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T15:00:00"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))

        # (the boundary condition is GTE)
        self.assertTrue(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T16:00:42"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))

        # Rises in reservoir volume taint the entire range
        self.assertFalse(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T15:55:00"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))

        # Any values of 0 taint the entire range
        i_dates.append(datetime.fromisoformat("2016-01-30T20:37:00"))
        i_volumes.append(0)
        self.assertFalse(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T16:40:00"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))

        # As long as the 0 is within the date interval bounds
        self.assertTrue(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T16:40:00"),
            datetime.fromisoformat("2016-01-30T19:40:00"), self.WITHIN))

    def test_non_continuous_reservoir_values(self):
        (i_dates, i_volumes) = self.load_reservoir_fixture(
            "reservoir_history_with_continuity_holes")

        self.assertTrue(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T18:30:00"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))
        self.assertFalse(is_continuous(
            i_dates, i_volumes, datetime.fromisoformat("2016-01-30T17:30:00"),
            datetime.fromisoformat("2016-01-30T20:40:00"), self.WITHIN))

    # did not include testIOBFromSuspend, testIOBFromDoses, and
    # testIOBFromNoDoses because they use the Walsh insulin model

    """ Tests for insulin_on_board """

    """
    func testIOBFromSuspend() {
        let input = loadDoseFixture("suspend_dose")
        let reconciledOutput = loadDoseFixture("suspend_dose_reconciled")
        let normalizedOutput = loadDoseFixture("suspend_dose_reconciled_normalized")
        let iobOutput = loadInsulinValueFixture("suspend_dose_reconciled_normalized_iob")
        let basals = loadBasalRateScheduleFixture("basal")
        let insulinModel = WalshInsulinModel(actionDuration: TimeInterval(hours: 4))

        let reconciled = input.reconciled()

        XCTAssertEqual(reconciledOutput.count, reconciled.count)

        for (expected, calculated) in zip(reconciledOutput, reconciled) {
            XCTAssertEqual(expected.startDate, calculated.startDate)
            XCTAssertEqual(expected.endDate, calculated.endDate)
            XCTAssertEqual(expected.value, calculated.value)
            XCTAssertEqual(expected.unit, calculated.unit)
        }

        let normalized = reconciled.annotated(with: basals)

        XCTAssertEqual(normalizedOutput.count, normalized.count)

        for (expected, calculated) in zip(normalizedOutput, normalized) {
            XCTAssertEqual(expected.startDate, calculated.startDate)
            XCTAssertEqual(expected.endDate, calculated.endDate)
            XCTAssertEqual(expected.value, calculated.netBasalUnitsPerHour, accuracy: Double(Float.ulpOfOne))
            XCTAssertEqual(expected.unit, calculated.unit)
        }

        let iob = normalized.insulinOnBoard(model: insulinModel)

        XCTAssertEqual(iobOutput.count, iob.count)

        for (expected, calculated) in zip(iobOutput, iob) {
            XCTAssertEqual(expected.startDate, calculated.startDate)
            XCTAssertEqual(expected.value, calculated.value, accuracy: Double(Float.ulpOfOne))
        }
    
    def test_iob_from_suspend(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("suspend_dose")
        
        (r_types, r_start_dates, r_end_dates, r_values, r_scheduled_basal_rates
         ) = self.load_dose_fixture("suspend_dose_reconciled")
        
        (n_types, n_start_dates, n_end_dates, n_values, n_scheduled_basal_rates
         ) = self.load_dose_fixture("suspend_dose_reconciled_normalized")

        (out_dates, out_insulin_values) = self.load_insulin_value_fixture(
            "suspend_dose_reconciled_normalized_iob")

        model = self.WALSH_MODEL
    """

    def test_iob_from_doses(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("normalized_doses")

        (out_dates, out_insulin_values) = self.load_insulin_value_fixture(
            "iob_from_doses_output_new")

        model = self.WALSH_MODEL

        (dates, insulin_values) = insulin_on_board(
            i_types, i_start_dates, i_end_dates, i_values,
            i_scheduled_basal_rates, model)

        self.assertEqual(len(out_dates), len(dates))

        for i in range(0, len(out_dates)):
            self.assertEqual(out_dates[i], dates[i])
            self.assertAlmostEqual(out_insulin_values[i], insulin_values[i], 1)
            
    """
    func testIOBFromNoDoses() {
        let input: [DoseEntry] = []
        let insulinModel = WalshInsulinModel(actionDuration: TimeInterval(hours: 4))

        let iob = input.insulinOnBoard(model: insulinModel)

        XCTAssertEqual(0, iob.count)
    }
    """
    def test_iob_from_no_doses(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = ([], [], [], [], [])

        model = self.WALSH_MODEL

        (dates, insulin_values) = insulin_on_board(
            i_types, i_start_dates, i_end_dates, i_values,
            i_scheduled_basal_rates, model)

        self.assertEqual(0, len(dates))

    def test_iob_from_doses_exponential(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("normalized_doses")

        (out_dates, out_insulin_values) = self.load_insulin_value_fixture(
            "iob_from_doses_exponential_output_new")

        model = self.MODEL

        (dates, insulin_values) = insulin_on_board(
            i_types, i_start_dates, i_end_dates, i_values,
            i_scheduled_basal_rates, model)

        self.assertEqual(len(out_dates), len(dates))

        for i in range(0, len(out_dates)):
            self.assertEqual(out_dates[i], dates[i])
            self.assertAlmostEqual(out_insulin_values[i], insulin_values[i], 2)

    def test_iob_from_bolus(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("bolus_dose")

        for hour in [2, 3, 4, 5, 5.2, 6, 7]:
            model = [hour]
            (out_dates, out_insulin_values) = self.load_insulin_value_fixture(
                "iob_from_bolus_" + str(int(hour*60)) + "min_output")

            (dates, insulin_values) = insulin_on_board(
                i_types, i_start_dates, i_end_dates, i_values,
                i_scheduled_basal_rates, model)

            self.assertEqual(len(out_dates), len(dates))

            for i in range(0, len(out_dates)):
                self.assertEqual(out_dates[i], dates[i])
                self.assertAlmostEqual(out_insulin_values[i],
                                       insulin_values[i], 1)

    def test_iob_from_bolus_exponential(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("bolus_dose")

        (out_dates, out_insulin_values) = self.load_insulin_value_fixture(
            "iob_from_bolus_exponential_output")

        model = self.MODEL

        (dates, insulin_values) = insulin_on_board(
            i_types, i_start_dates, i_end_dates, i_values,
            i_scheduled_basal_rates, model)

        self.assertEqual(len(out_dates), len(dates))

        for i in range(0, len(out_dates)):
            self.assertEqual(out_dates[i], dates[i])
            self.assertAlmostEqual(out_insulin_values[i], insulin_values[i], 1)

        """ Tests for percent_effect_remaining """
    def test_insulin_on_board_limits_for_exponential_model(self):
        # tests for adult curve (peak = 75 mins)
        self.assertAlmostEqual(1, percent_effect_remaining(-1, 360, 75), 3)
        self.assertAlmostEqual(1, percent_effect_remaining(0, 360, 75), 3)
        self.assertAlmostEqual(0, percent_effect_remaining(360, 360, 75), 3)
        self.assertAlmostEqual(0, percent_effect_remaining(361, 360, 75), 3)

        # test at random point
        self.assertAlmostEqual(0.5110493617156,
                               percent_effect_remaining(108, 361, 75), 3)

        # test for child curve (peak = 65 mins)
        self.assertAlmostEqual(0.6002510111374046,
                               percent_effect_remaining(82, 360, 65), 3)

    """ Tests for reconceiled """
    def test_normalize_reservoir_doses(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("reservoir_history_with_rewind_and_" +
                                    "prime_output")

        (out_types, out_start_dates, out_end_dates, out_values,
         out_scheduled_basal_rates) = self.load_dose_fixture(
            "normalized_reservoir_history_output")

        (start_times, rates, minutes) = self.load_basal_rate_schedule_fixture(
            "basal")

        (types, start_dates, end_dates, values, scheduled_basal_rates
         ) = annotated(i_types, i_start_dates, i_end_dates, i_values,
                       i_scheduled_basal_rates, start_times, rates, minutes,
                       convert_to_units_hr=True)

        self.assertEqual(len(out_types), len(types))

        for i in range(0, len(out_types)):
            self.assertEqual(out_start_dates[i], start_dates[i])
            self.assertEqual(out_end_dates[i], end_dates[i])
            self.assertAlmostEqual(out_values[i], values[i], 2)
            self.assertEqual(
                out_scheduled_basal_rates[i], scheduled_basal_rates[i])

    def test_normalize_edgecase_doses(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("normalize_edge_case_doses_input")

        (out_types, out_start_dates, out_end_dates, out_values,
         out_scheduled_basal_rates) = self.load_dose_fixture(
            "normalize_edge_case_doses_output")

        (start_times, rates, minutes) = self.load_basal_rate_schedule_fixture(
            "basal")

        (types, start_dates, end_dates, values, scheduled_basal_rates
         ) = annotated(i_types, i_start_dates, i_end_dates, i_values,
                       i_scheduled_basal_rates, start_times, rates, minutes)

        self.assertEqual(len(out_types), len(types))

        for i in range(0, len(out_types)):
            self.assertEqual(out_start_dates[i], start_dates[i])
            self.assertEqual(out_end_dates[i], end_dates[i])
            self.assertAlmostEqual(out_values[i], values[i] -
                scheduled_basal_rates[i], 2)

    """
    func testReconcileTempBasals() {
        // Fixture contains numerous overlapping temp basals, as well as a Suspend event interleaved with a temp basal
        let input = loadDoseFixture("reconcile_history_input")
        let output = loadDoseFixture("reconcile_history_output").sorted { $0.startDate < $1.startDate }

        let doses = input.reconciled().sorted { $0.startDate < $1.startDate }

        XCTAssertEqual(output.count, doses.count)

        for (expected, calculated) in zip(output, doses) {
            XCTAssertEqual(expected.startDate, calculated.startDate)
            XCTAssertEqual(expected.endDate, calculated.endDate)
            XCTAssertEqual(expected.value, calculated.value)
            XCTAssertEqual(expected.unit, calculated.unit)
            XCTAssertEqual(expected.syncIdentifier, calculated.syncIdentifier)
        }
    }

    func testReconcileResumeBeforeRewind() {
        let input = loadDoseFixture("reconcile_resume_before_rewind_input")
        let output = loadDoseFixture("reconcile_resume_before_rewind_output")

        let doses = input.reconciled()

        XCTAssertEqual(output.count, doses.count)

        for (expected, calculated) in zip(output, doses) {
            XCTAssertEqual(expected.startDate, calculated.startDate)
            XCTAssertEqual(expected.endDate, calculated.endDate)
            XCTAssertEqual(expected.value, calculated.value)
            XCTAssertEqual(expected.unit, calculated.unit)
            XCTAssertEqual(expected.syncIdentifier, calculated.syncIdentifier)
        }
    }

    """
    """ Tests for glucose_effect """
    def test_glucose_effect_from_bolus(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("bolus_dose")

        (out_dates, out_effect_values) = self.load_glucose_effect_fixture(
            "effect_from_bolus_output")

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.WALSH_MODEL

        effect_dates, effect_values = glucose_effects(
            i_types, i_start_dates, i_end_dates, i_values,
            i_scheduled_basal_rates, model, sensitivity_start_dates,
            sensitivity_end_dates, sensitivity_values)

        self.assertEqual(len(out_dates), len(effect_dates))

        for i in range(0, len(out_dates)):
            self.assertEqual(out_dates[i], effect_dates[i])
            self.assertAlmostEqual(out_effect_values[i], effect_values[i], 0)

    def test_glucose_effect_from_bolus_exponential(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("bolus_dose")

        (out_dates, out_effect_values) = self.load_glucose_effect_fixture(
            "effect_from_bolus_output_exponential")

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.MODEL

        effect_dates, effect_values = glucose_effects(
            i_types, i_start_dates, i_end_dates, i_values,
            i_scheduled_basal_rates, model, sensitivity_start_dates,
            sensitivity_end_dates, sensitivity_values)

        self.assertEqual(len(out_dates), len(effect_dates))

        for i in range(0, len(out_dates)):
            self.assertEqual(out_dates[i], effect_dates[i])
            self.assertAlmostEqual(out_effect_values[i], effect_values[i], 0)

    def test_glucose_effect_from_short_temp_basal(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("short_basal_dose")

        (out_dates, out_effect_values) = self.load_glucose_effect_fixture(
            "effect_from_short_basal_output")

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.WALSH_MODEL

        effect_dates, effect_values = glucose_effects(
            i_types, i_start_dates, i_end_dates, i_values,
            i_scheduled_basal_rates, model, sensitivity_start_dates,
            sensitivity_end_dates, sensitivity_values)

        self.assertEqual(len(out_dates), len(effect_dates))

        for i in range(0, len(out_dates)):
            self.assertEqual(out_dates[i], effect_dates[i])
            self.assertAlmostEqual(out_effect_values[i], effect_values[i], 0)

    def test_glucose_effect_from_temp_basal(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("basal_dose")

        (out_dates, out_effect_values) = self.load_glucose_effect_fixture(
            "effect_from_basal_output")

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.WALSH_MODEL

        effect_dates, effect_values = glucose_effects(
            i_types, i_start_dates, i_end_dates, i_values,
            i_scheduled_basal_rates, model, sensitivity_start_dates,
            sensitivity_end_dates, sensitivity_values)

        self.assertEqual(len(out_dates), len(effect_dates))

        for i in range(0, len(out_dates)):
            self.assertEqual(out_dates[i], effect_dates[i])
            self.assertAlmostEqual(out_effect_values[i], effect_values[i], -1)

    def test_glucose_effect_from_temp_basal_exponential(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("basal_dose")

        (out_dates, out_effect_values) = self.load_glucose_effect_fixture(
            "effect_from_basal_output_exponential")

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.MODEL

        effect_dates, effect_values = glucose_effects(
            i_types, i_start_dates, i_end_dates, i_values,
            i_scheduled_basal_rates, model, sensitivity_start_dates,
            sensitivity_end_dates, sensitivity_values)

        self.assertEqual(len(out_dates), len(effect_dates))

        for i in range(0, len(out_dates)):
            self.assertEqual(out_dates[i], effect_dates[i])
            self.assertAlmostEqual(out_effect_values[i], effect_values[i], -1)

    def test_glucose_effect_from_history(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("normalized_doses")

        (out_dates, out_effect_values) = self.load_glucose_effect_fixture(
            "effect_from_history_output")

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.WALSH_MODEL

        effect_dates, effect_values = glucose_effects(
            i_types, i_start_dates, i_end_dates, i_values,
            i_scheduled_basal_rates, model, sensitivity_start_dates,
            sensitivity_end_dates, sensitivity_values)

        self.assertEqual(len(out_dates), len(effect_dates))

        for i in range(0, len(out_dates)):
            self.assertEqual(out_dates[i], effect_dates[i])
            self.assertAlmostEqual(out_effect_values[i], effect_values[i], -1)

    def test_glucose_effect_from_history_exponential(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = self.load_dose_fixture("normalized_doses")

        (out_dates, out_effect_values) = self.load_glucose_effect_fixture(
            "effect_from_history_output_exponential")

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.MODEL

        effect_dates, effect_values = glucose_effects(
            i_types, i_start_dates, i_end_dates, i_values,
            i_scheduled_basal_rates, model, sensitivity_start_dates,
            sensitivity_end_dates, sensitivity_values)

        self.assertEqual(len(out_dates), len(effect_dates))

        for i in range(0, len(out_dates)):
            self.assertEqual(out_dates[i], effect_dates[i])
            self.assertAlmostEqual(out_effect_values[i], effect_values[i], -1)

    def test_glucose_effect_from_no_doses(self):
        (i_types, i_start_dates, i_end_dates, i_values, i_scheduled_basal_rates
         ) = ([], [], [], [], [])

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.MODEL

        effect_dates, effect_values = glucose_effects(
            i_types, i_start_dates, i_end_dates, i_values,
            i_scheduled_basal_rates, model, sensitivity_start_dates,
            sensitivity_end_dates, sensitivity_values)

        self.assertEqual(0, len(effect_dates))


if __name__ == '__main__':
    unittest.main()
