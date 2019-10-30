#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 09:00:27 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKitTests/InsulinMathTests.swift
"""
# pylint: disable = R0201, C0111, W0105, W0612, C0200, R0914, R0904, C0302
# disable pylint warnings for "method could be function", String statement
# has no effect, unused variable (for tuple unpacking), enumerate instead
# of range
import unittest
from datetime import datetime, time
import numpy

from pyloopkit.dose import DoseType
from pyloopkit.exponential_insulin_model import percent_effect_remaining
from pyloopkit.insulin_math import (dose_entries, is_continuous, insulin_on_board,
                          glucose_effects, annotated, reconciled,
                          total_delivery, trim, overlay_basal_schedule)
from .loop_kit_tests import load_fixture


class TestInsulinKitFunctions(unittest.TestCase):
    """ unittest class to run InsulinKit tests."""
    WITHIN = 30

    MODEL = [360, 75]
    WALSH_MODEL = [4]

    INSULIN_SENSITIVITY_START_DATES = [time(0, 0)]
    INSULIN_SENSITIVITY_END_DATES = [time(23, 59)]
    INSULIN_SENSITIVITY_VALUES = [40]

    MULTIPLE_INSULIN_SENSITIVITY_START_DATES = [
        time(0, 0), time(19, 00), time(21, 00)
    ]
    MULTIPLE_INSULIN_SENSITIVITY_END_DATES = [
        time(19, 00), time(21, 00), time(0, 0)
    ]
    MULTIPLE_INSULIN_SENSITIVITY_VALUES = [40, 140, 10]

    TRIM_END_DATE = datetime.fromisoformat("2015-10-15T22:25:50")
    DISTANT_FUTURE = datetime.fromisoformat("2050-01-01T00:00:00")

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

        dates = [
            datetime.fromisoformat(dict_.get("date"))
            for dict_ in fixture
        ]
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

        dose_types = [
            DoseType.from_str(
                dict_.get("type")
            ) or "!" for dict_ in fixture
        ]
        start_dates = [
            datetime.fromisoformat(dict_.get("start_at"))
            for dict_ in fixture
        ]
        end_dates = [
            datetime.fromisoformat(dict_.get("end_at"))
            for dict_ in fixture
        ]
        values = [dict_.get("amount") for dict_ in fixture]
        # not including description, unit, and raw bc not relevent
        scheduled_basal_rates = [
            dict_.get("scheduled") or 0 for dict_ in fixture
        ]

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

        start_dates = [
            datetime.fromisoformat(dict_.get("date"))
            for dict_ in fixture
        ]
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

        dates = [
            datetime.fromisoformat(dict_.get("date"))
            for dict_ in fixture
        ]
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

        start_times = [
            datetime.strptime(dict_.get("start"), "%H:%M:%S").time()
            for dict_ in fixture
        ]
        rates = [dict_.get("rate") for dict_ in fixture]
        minutes = [dict_.get("minutes") for dict_ in fixture]

        assert len(start_times) == len(rates) == len(minutes),\
            "expected output shape to match"

        return (start_times, rates, minutes)

    """ Tests for dose_entries """
    def test_dose_entries_from_reservoir_values(self):
        (i_dates, i_volumes) = self.load_reservoir_fixture(
            "reservoir_history_with_rewind_and_prime_input"
        )
        (expected_dose_types,
         expected_start_dates,
         expected_end_dates,
         expected_values,
         expected_scheduled_basal_rates
         ) = self.load_dose_fixture(
             "reservoir_history_with_rewind_and_prime_output"
             )

        expected_start_dates.reverse()
        expected_end_dates.reverse()
        expected_values.reverse()

        (dose_types,
         start_dates,
         end_dates,
         values) = dose_entries(
             i_dates, i_volumes
         )

        self.assertEqual(
            len(expected_start_dates), len(start_dates)
        )

        for i in range(0, len(expected_start_dates)):
            self.assertEqual(
                expected_start_dates[i], start_dates[i]
            )
            self.assertEqual(
                expected_end_dates[i], end_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], values[i], 2
            )

    """ Tests for is_continuous """
    def test_continuous_reservoir_values(self):
        (i_dates, i_volumes) = self.load_reservoir_fixture(
            "reservoir_history_with_rewind_and_prime_input"
        )
        self.assertTrue(
            is_continuous(
                i_dates,
                i_volumes,
                datetime.fromisoformat("2016-01-30T16:40:00"),
                datetime.fromisoformat("2016-01-30T20:40:00"),
                self.WITHIN
            )
        )

        # We don't assert whether it's "stale".
        self.assertTrue(
            is_continuous(
                i_dates,
                i_volumes,
                datetime.fromisoformat("2016-01-30T16:40:00"),
                datetime.fromisoformat("2016-01-30T22:40:00"),
                self.WITHIN
            )
        )
        self.assertTrue(
            is_continuous(
                i_dates,
                i_volumes,
                datetime.fromisoformat("2016-01-30T16:40:00"),
                datetime.now(),
                self.WITHIN
            )
        )

        # The values must extend the startDate boundary
        self.assertFalse(
            is_continuous(
                i_dates,
                i_volumes,
                datetime.fromisoformat("2016-01-30T15:00:00"),
                datetime.fromisoformat("2016-01-30T20:40:00"),
                self.WITHIN
            )
        )

        # (the boundary condition is GTE)
        self.assertTrue(
            is_continuous(
                i_dates,
                i_volumes,
                datetime.fromisoformat("2016-01-30T16:00:42"),
                datetime.fromisoformat("2016-01-30T20:40:00"),
                self.WITHIN
            )
        )

        # Rises in reservoir volume taint the entire range
        self.assertFalse(
            is_continuous(
                i_dates,
                i_volumes,
                datetime.fromisoformat("2016-01-30T15:55:00"),
                datetime.fromisoformat("2016-01-30T20:40:00"),
                self.WITHIN
            )
        )

        # Any values of 0 taint the entire range
        i_dates.append(datetime.fromisoformat("2016-01-30T20:37:00"))
        i_volumes.append(0)

        self.assertFalse(
            is_continuous(
                i_dates,
                i_volumes,
                datetime.fromisoformat("2016-01-30T16:40:00"),
                datetime.fromisoformat("2016-01-30T20:40:00"),
                self.WITHIN
            )
        )

        # As long as the 0 is within the date interval bounds
        self.assertTrue(
            is_continuous(
                i_dates,
                i_volumes,
                datetime.fromisoformat("2016-01-30T16:40:00"),
                datetime.fromisoformat("2016-01-30T19:40:00"),
                self.WITHIN
            )
        )

    def test_non_continuous_reservoir_values(self):
        (i_dates, i_volumes) = self.load_reservoir_fixture(
            "reservoir_history_with_continuity_holes"
        )

        self.assertTrue(
            is_continuous(
                i_dates,
                i_volumes,
                datetime.fromisoformat("2016-01-30T18:30:00"),
                datetime.fromisoformat("2016-01-30T20:40:00"),
                self.WITHIN
            )
        )
        self.assertFalse(
            is_continuous(
                i_dates,
                i_volumes,
                datetime.fromisoformat("2016-01-30T17:30:00"),
                datetime.fromisoformat("2016-01-30T20:40:00"),
                self.WITHIN
            )
        )

    """ Tests for insulin_on_board """
    def test_iob_from_suspend(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values
         ) = self.load_dose_fixture("suspend_dose")[0:4]

        (r_types,
         r_start_dates,
         r_end_dates,
         r_values,
         r_scheduled_basal_rates
         ) = self.load_dose_fixture("suspend_dose_reconciled")

        (n_types,
         n_start_dates,
         n_end_dates,
         n_values,
         n_scheduled_basal_rates
         ) = self.load_dose_fixture("suspend_dose_reconciled_normalized")

        (out_dates,
         out_insulin_values
         ) = self.load_insulin_value_fixture(
             "suspend_dose_reconciled_normalized_iob"
             )

        (start_times,
         rates,
         minutes
         ) = self.load_basal_rate_schedule_fixture("basal")

        model = self.WALSH_MODEL

        (r_out_types,
         r_out_start_dates,
         r_out_end_dates,
         r_out_values
         ) = reconciled(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values
             )

        self.assertEqual(
            len(r_types), len(r_out_types)
        )
        for i in range(0, len(r_types)):
            self.assertEqual(
                r_start_dates[i], r_out_start_dates[i]
            )
            self.assertEqual(
                r_end_dates[i], r_out_end_dates[i]
            )
            self.assertAlmostEqual(
                r_values[i], r_out_values[i], 2
            )

        (n_out_types,
         n_out_start_dates,
         n_out_end_dates,
         n_out_values,
         n_out_scheduled_rates) = annotated(
             r_out_types,
             r_out_start_dates,
             r_out_end_dates,
             r_out_values,
             start_times,
             rates,
             minutes
             )

        self.assertEqual(
            len(n_types), len(n_out_types)
        )
        for i in range(0, len(r_types)):
            self.assertEqual(
                n_start_dates[i], n_out_start_dates[i]
            )
            self.assertEqual(
                n_end_dates[i], n_out_end_dates[i]
            )
            self.assertAlmostEqual(
                n_values[i],
                n_out_values[i] - n_out_scheduled_rates[i], 2
            )

        (dates,
         insulin_values
         ) = insulin_on_board(
             n_out_types,
             n_out_start_dates,
             n_out_end_dates,
             n_out_values,
             n_out_scheduled_rates,
             model
             )

        self.assertEqual(
            len(out_dates), len(dates)
        )
        for i in range(0, len(out_dates)):
            self.assertEqual(
                out_dates[i], dates[i]
            )
            self.assertAlmostEqual(
                out_insulin_values[i], insulin_values[i], 2
            )

    def test_iob_from_doses(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("normalized_doses")

        (expected_dates,
         expected_insulin_values
         ) = self.load_insulin_value_fixture(
             "iob_from_doses_output_new"
             )

        model = self.WALSH_MODEL

        (dates,
         insulin_values
         ) = insulin_on_board(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values,
             i_scheduled_basal_rates,
             model
             )

        self.assertEqual(
            len(expected_dates), len(dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], dates[i]
            )
            self.assertTrue(
                -0.5 < expected_insulin_values[i] - insulin_values[i] < 0.5
            )

    def test_iob_from_no_doses(self):
        model = self.WALSH_MODEL

        (dates,
         insulin_values
         ) = insulin_on_board([], [], [], [], [], model)

        self.assertEqual(0, len(dates))

    def test_iob_from_doses_exponential(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("normalized_doses")

        (expected_dates,
         expected_insulin_values
         ) = self.load_insulin_value_fixture(
             "iob_from_doses_exponential_output_new"
             )

        model = self.MODEL

        (dates,
         insulin_values
         ) = insulin_on_board(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values,
             i_scheduled_basal_rates,
             model
             )

        self.assertEqual(
            len(expected_dates), len(dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], dates[i]
            )
            self.assertTrue(
                -0.5 < expected_insulin_values[i] - insulin_values[i] < 0.5
            )

    def test_iob_from_bolus(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("bolus_dose")

        for hour in [2, 3, 4, 5, 5.2, 6, 7]:
            model = [hour]
            (expected_dates,
             expected_insulin_values
             ) = self.load_insulin_value_fixture(
                 "iob_from_bolus_" + str(int(hour*60)) + "min_output"
                 )

            (dates,
             insulin_values
             ) = insulin_on_board(
                 i_types,
                 i_start_dates,
                 i_end_dates,
                 i_values,
                 i_scheduled_basal_rates,
                 model
                 )

            self.assertEqual(
                len(expected_dates), len(dates)
            )

            for i in range(0, len(expected_dates)):
                self.assertEqual(
                    expected_dates[i], dates[i]
                )
                self.assertAlmostEqual(
                    expected_insulin_values[i], insulin_values[i], 2
                )

    def test_iob_from_bolus_exponential(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("bolus_dose")

        (expected_dates,
         expected_insulin_values
         ) = self.load_insulin_value_fixture(
             "iob_from_bolus_exponential_output"
             )

        model = self.MODEL

        (dates,
         insulin_values
         ) = insulin_on_board(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values,
             i_scheduled_basal_rates,
             model
             )

        self.assertEqual(
            len(expected_dates), len(dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], dates[i]
            )
            self.assertAlmostEqual(
                expected_insulin_values[i], insulin_values[i], 2
            )

    def test_iob_from_reservoir_doses(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("normalized_reservoir_history_output")

        (expected_dates,
         expected_insulin_values
         ) = self.load_insulin_value_fixture("iob_from_reservoir_output")

        model = self.WALSH_MODEL

        (dates,
         insulin_values
         ) = insulin_on_board(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values,
             i_scheduled_basal_rates,
             model
             )

        self.assertEqual(
            len(expected_dates), len(dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], dates[i]
            )
            self.assertTrue(
                -0.4 < expected_insulin_values[i] - insulin_values[i] < 0.4
            )

        """ Tests for percent_effect_remaining """
    def test_insulin_on_board_limits_for_exponential_model(self):
        # tests for adult curve (peak = 75 mins)
        self.assertAlmostEqual(
            1, percent_effect_remaining(-1, 360, 75), 3
        )
        self.assertAlmostEqual(
            1, percent_effect_remaining(0, 360, 75), 3
        )
        self.assertAlmostEqual(
            0, percent_effect_remaining(360, 360, 75), 3
        )
        self.assertAlmostEqual(
            0, percent_effect_remaining(361, 360, 75), 3
        )

        # test at random point
        self.assertAlmostEqual(
            0.5110493617156, percent_effect_remaining(108, 361, 75), 3
        )

        # test for child curve (peak = 65 mins)
        self.assertAlmostEqual(
            0.6002510111374046, percent_effect_remaining(82, 360, 65), 3
        )

    """ Tests for reconceiled """
    def test_normalize_reservoir_doses(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values
         ) = self.load_dose_fixture(
             "reservoir_history_with_rewind_and_prime_output"
             )[0:4]

        (expected_types,
         expected_start_dates,
         expected_end_dates,
         expected_values,
         expected_scheduled_basal_rates
         ) = self.load_dose_fixture(
             "normalized_reservoir_history_output"
             )

        (start_times,
         rates,
         minutes
         ) = self.load_basal_rate_schedule_fixture("basal")

        (types,
         start_dates,
         end_dates,
         values,
         scheduled_basal_rates
         ) = annotated(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values,
             start_times,
             rates,
             minutes
             )

        self.assertEqual(
            len(expected_types), len(types)
        )

        for i in range(0, len(expected_types)):
            self.assertEqual(
                expected_start_dates[i], start_dates[i]
            )
            self.assertEqual(
                expected_end_dates[i], end_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], values[i], 2
            )
            self.assertEqual(
                expected_scheduled_basal_rates[i], scheduled_basal_rates[i]
            )

    def test_normalize_edgecase_doses(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values
         ) = self.load_dose_fixture("normalize_edge_case_doses_input")[0:4]

        (expected_types,
         expected_start_dates,
         expected_end_dates,
         expected_values,
         expected_scheduled_basal_rates
         ) = self.load_dose_fixture("normalize_edge_case_doses_output")

        (start_times,
         rates,
         minutes
         ) = self.load_basal_rate_schedule_fixture("basal")

        (types,
         start_dates,
         end_dates,
         values,
         scheduled_basal_rates
         ) = annotated(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values,
             start_times,
             rates,
             minutes,
             convert_to_units_hr=False
             )

        self.assertEqual(
            len(expected_types), len(types)
        )

        for i in range(0, len(expected_types)):
            self.assertEqual(
                expected_start_dates[i], start_dates[i]
            )
            self.assertEqual(
                expected_end_dates[i], end_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], values[i] - scheduled_basal_rates[i], 2
            )

    def test_reconcile_temp_basals(self):
        # Fixture contains numerous overlapping temp basals, as well as a
        # Suspend event interleaved with a temp basal
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values
         ) = self.load_dose_fixture("reconcile_history_input")[0:4]

        (expected_types,
         expected_start_dates,
         expected_end_dates,
         expected_values,
         expected_scheduled_basal_rates
         ) = self.load_dose_fixture("reconcile_history_output")

        (types,
         start_dates,
         end_dates,
         values
         ) = reconciled(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values
             )

        # sort the lists because they're out of order due to all the
        # meals during temp basals
        unsort_types = numpy.array(types)
        start_dates = numpy.array(start_dates)
        unsort_end_dates = numpy.array(end_dates)
        unsort_values = numpy.array(values)

        sort_ind = start_dates.argsort()
        types = unsort_types[sort_ind]
        start_dates.sort()
        end_dates = unsort_end_dates[sort_ind]
        values = unsort_values[sort_ind]

        self.assertEqual(
            len(expected_types), len(types)
        )

        for i in range(0, len(expected_types)):
            self.assertEqual(
                expected_start_dates[i], start_dates[i]
            )
            self.assertEqual(
                expected_end_dates[i], end_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], values[i], 2
            )

    def test_reconcile_resume_before_rewind(self):
        # Fixture contains numerous overlapping temp basals, as well as a
        # Suspend event interleaved with a temp basal
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values
         ) = self.load_dose_fixture(
             "reconcile_resume_before_rewind_input"
             )[0:4]

        (expected_types,
         expected_start_dates,
         expected_end_dates,
         expected_values,
         expected_scheduled_basal_rates
         ) = self.load_dose_fixture("reconcile_resume_before_rewind_output")

        (types,
         start_dates,
         end_dates,
         values
         ) = reconciled(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values
             )

        self.assertEqual(
            len(expected_types), len(types)
        )

        for i in range(0, len(expected_types)):
            self.assertEqual(
                expected_start_dates[i], start_dates[i]
            )
            self.assertEqual(
                expected_end_dates[i], end_dates[i]
            )
            self.assertAlmostEqual(
                expected_values[i], values[i], 2
            )

    """ Tests for glucose_effect """
    def test_glucose_effect_from_bolus(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("bolus_dose")

        (expected_dates,
         expected_effect_values
         ) = self.load_glucose_effect_fixture("effect_from_bolus_output")

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.WALSH_MODEL

        (effect_dates,
         effect_values
         ) = glucose_effects(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values,
             i_scheduled_basal_rates,
             model,
             sensitivity_start_dates,
             sensitivity_end_dates,
             sensitivity_values
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertAlmostEqual(
                expected_effect_values[i], effect_values[i], 0
            )

    def test_glucose_effect_from_bolus_exponential(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("bolus_dose")

        (expected_dates,
         expected_effect_values
         ) = self.load_glucose_effect_fixture(
             "effect_from_bolus_output_exponential"
             )

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.MODEL

        (effect_dates,
         effect_values
         ) = glucose_effects(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values,
             i_scheduled_basal_rates,
             model,
             sensitivity_start_dates,
             sensitivity_end_dates,
             sensitivity_values
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertAlmostEqual(
                expected_effect_values[i], effect_values[i], 0
            )

    def test_glucose_effect_from_short_temp_basal(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("short_basal_dose")

        (expected_dates,
         expected_effect_values
         ) = self.load_glucose_effect_fixture("effect_from_short_basal_output")

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.WALSH_MODEL

        (effect_dates,
         effect_values
         ) = glucose_effects(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values,
             i_scheduled_basal_rates,
             model,
             sensitivity_start_dates,
             sensitivity_end_dates,
             sensitivity_values
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertAlmostEqual(
                expected_effect_values[i], effect_values[i], 2
            )

    def test_glucose_effect_from_temp_basal(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("basal_dose")

        (expected_dates,
         expected_effect_values
         ) = self.load_glucose_effect_fixture("effect_from_basal_output")

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.WALSH_MODEL

        (effect_dates,
         effect_values
         ) = glucose_effects(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values,
             i_scheduled_basal_rates,
             model,
             sensitivity_start_dates,
             sensitivity_end_dates,
             sensitivity_values
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertTrue(
                -1 < expected_effect_values[i] - effect_values[i] < 1
            )

    def test_glucose_effect_from_temp_basal_exponential(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("basal_dose")

        (expected_dates,
         expected_effect_values
         ) = self.load_glucose_effect_fixture(
             "effect_from_basal_output_exponential"
             )

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.MODEL

        (effect_dates,
         effect_values
         ) = glucose_effects(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values,
             i_scheduled_basal_rates,
             model,
             sensitivity_start_dates,
             sensitivity_end_dates,
             sensitivity_values
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertTrue(
                -1 < expected_effect_values[i] - effect_values[i] < 1
            )

    def test_glucose_effect_from_history(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("normalized_doses")

        (expected_dates,
         expected_effect_values
         ) = self.load_glucose_effect_fixture("effect_from_history_output")

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.WALSH_MODEL

        (effect_dates,
         effect_values
         ) = glucose_effects(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values,
             i_scheduled_basal_rates,
             model,
             sensitivity_start_dates,
             sensitivity_end_dates,
             sensitivity_values
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertTrue(
                -3 < expected_effect_values[i] - effect_values[i] < 3
            )

    def test_glucose_effect_from_history_exponential(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("normalized_doses")

        (expected_dates,
         expected_effect_values
         ) = self.load_glucose_effect_fixture(
             "effect_from_history_output_exponential"
             )

        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.MODEL

        (effect_dates,
         effect_values
         ) = glucose_effects(
             i_types,
             i_start_dates,
             i_end_dates,
             i_values,
             i_scheduled_basal_rates,
             model,
             sensitivity_start_dates,
             sensitivity_end_dates,
             sensitivity_values
             )

        self.assertEqual(
            len(expected_dates), len(effect_dates)
        )

        for i in range(0, len(expected_dates)):
            self.assertEqual(
                expected_dates[i], effect_dates[i]
            )
            self.assertTrue(
                -3 < expected_effect_values[i] - effect_values[i] < 3
            )

    def test_glucose_effect_from_no_doses(self):
        sensitivity_start_dates = self.INSULIN_SENSITIVITY_START_DATES
        sensitivity_end_dates = self.INSULIN_SENSITIVITY_END_DATES
        sensitivity_values = self.INSULIN_SENSITIVITY_VALUES
        model = self.MODEL

        (effect_dates,
         effect_values
         ) = glucose_effects(
             [], [], [], [], [],
             model,
             sensitivity_start_dates,
             sensitivity_end_dates,
             sensitivity_values
             )

        self.assertEqual(
            0, len(effect_dates)
        )

    """ Tests for total_delivery """
    def test_total_delivery(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("normalize_edge_case_doses_input")

        total = total_delivery(
            i_types,
            i_start_dates,
            i_end_dates,
            i_values
        )

        self.assertAlmostEqual(18.8, total, 2)

    """ Tests for trim """
    def test_trim_continuing_doses(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values,
         i_scheduled_basal_rates
         ) = self.load_dose_fixture("normalized_doses")

        # put the dose lists in order of start time
        unsort_types = numpy.array(i_types)
        i_start_dates = numpy.array(i_start_dates)
        unsort_end_dates = numpy.array(i_end_dates)
        unsort_values = numpy.array(i_values)

        sort_ind = i_start_dates.argsort()
        i_types = unsort_types[sort_ind]
        i_start_dates.sort()
        i_end_dates = unsort_end_dates[sort_ind]
        i_values = unsort_values[sort_ind]

        assert len(i_types) == len(i_start_dates) == len(i_end_dates)\
            == len(i_values), "expected fixture to include data for all doses"

        trimmed = trim(
            i_types[-1],
            i_start_dates[-1],
            i_end_dates[-1],
            i_values[-1],
            i_scheduled_basal_rates[-1],
            end_interval=self.TRIM_END_DATE
        )
        self.assertEqual(
            self.TRIM_END_DATE, trimmed[2]
        )

    def test_doses_overlay_basal_profile(self):
        (i_types,
         i_start_dates,
         i_end_dates,
         i_values
         ) = self.load_dose_fixture("reconcile_history_output")[0:4]

        # put the dose lists in order of start time
        unsort_types = numpy.array(i_types)
        i_start_dates = numpy.array(i_start_dates)
        unsort_end_dates = numpy.array(i_end_dates)
        unsort_values = numpy.array(i_values)

        sort_ind = i_start_dates.argsort()
        i_types = list(unsort_types[sort_ind])
        i_start_dates.sort()
        i_end_dates = list(unsort_end_dates[sort_ind])
        i_values = list(unsort_values[sort_ind])

        (start_times,
         rates,
         minutes
         ) = self.load_basal_rate_schedule_fixture("basal")

        (out_types,
         out_start_dates,
         out_end_dates,
         out_values,
         out_scheduled_basal_rates
         ) = self.load_dose_fixture("doses_overlay_basal_profile_output")

        (a_types,
         a_start_dates,
         a_end_dates,
         a_values,
         a_scheduled_basal_rates
         ) = annotated(
             i_types,
             list(i_start_dates),
             i_end_dates,
             i_values,
             start_times,
             rates,
             minutes,
             convert_to_units_hr=False
             )

        (types,
         starts,
         ends,
         values
         ) = overlay_basal_schedule(
             a_types,
             a_start_dates,
             a_end_dates,
             a_values,
             start_times,
             rates,
             minutes,
             datetime.fromisoformat("2016-02-15T14:01:04"),
             self.DISTANT_FUTURE,
             True
             )

        self.assertEqual(
            len(out_types), len(types)
        )

        for i in range(0, len(out_types)):
            self.assertEqual(
                out_start_dates[i], starts[i]
            )
            self.assertEqual(
                out_end_dates[i], ends[i]
            )
            self.assertEqual(
                out_values[i], values[i]
            )

        (a_trim_types,
         a_trim_start_dates,
         a_trim_end_dates,
         a_trim_values,
         a_trim_scheduled_basal_rates
         ) = annotated(
             i_types[0:len(i_types) - 11],
             list(i_start_dates)[0:len(i_types) - 11],
             i_end_dates[0:len(i_types) - 11],
             i_values[0:len(i_types) - 11],
             start_times,
             rates,
             minutes,
             convert_to_units_hr=False
             )

        (t_types,
         t_starts,
         t_ends,
         t_values
         ) = overlay_basal_schedule(
             a_trim_types,
             a_trim_start_dates,
             a_trim_end_dates,
             a_trim_values,
             start_times,
             rates,
             minutes,
             datetime.fromisoformat("2016-02-15T14:01:04"),
             datetime.fromisoformat("2016-02-15T19:45:00"),
             True
             )

        self.assertEqual(
            len(out_types) - 14, len(t_types)
        )
        self.assertEqual(
            datetime.fromisoformat("2016-02-15T19:36:11"),
            t_ends[len(t_ends)-1]
        )

        (m_types,
         m_starts,
         m_ends,
         m_values
         ) = overlay_basal_schedule(
             i_types,
             list(i_start_dates),
             i_end_dates,
             i_values,
             start_times,
             rates,
             minutes,
             datetime.fromisoformat("2016-02-15T15:06:05"),
             self.DISTANT_FUTURE,
             True
             )

        self.assertEqual(
            len(out_types) - 2, len(m_types)
        )
        self.assertEqual(
            datetime.fromisoformat("2016-02-15T14:58:02"), t_ends[0]
        )


if __name__ == '__main__':
    unittest.main()
