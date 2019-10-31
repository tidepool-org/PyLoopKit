#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 16 15:41:18 2019

@author: annaquinlan
"""
# pylint: disable=C0111, C0411, W0105
import unittest
from datetime import datetime, timedelta

from . import path_grabber  # pylint: disable=unused-import
from pyloopkit.date import (date_floored_to_time_interval, date_ceiled_to_time_interval,
                  time_interval_since_reference_date, time_interval_since)

REF_DATE = datetime(2001, 1, 1, 0, 0, 0)


class TestDateFunctions(unittest.TestCase):

    """ Tests for date_ceiled_to_time_interval """
    def test_date_ceiled_to_interval(self):
        calendar = datetime.now()
        five_01 = calendar.replace(hour=5, minute=0, second=1, microsecond=0)
        five_05 = calendar.replace(hour=5, minute=5, second=0, microsecond=0)
        self.assertEqual(five_05, date_ceiled_to_time_interval(five_01, 5))
        self.assertEqual(five_01, date_ceiled_to_time_interval(five_01, 0))

        six = calendar.replace(hour=6, minute=0, second=0, microsecond=0)
        self.assertEqual(six, date_ceiled_to_time_interval(five_01, 60))

        self.assertEqual(five_05, date_ceiled_to_time_interval(five_05, 5))

        five_47 = calendar.replace(hour=5, minute=47, second=58, microsecond=0)
        five_50 = calendar.replace(hour=5, minute=50, second=0, microsecond=0)
        self.assertEqual(five_50, date_ceiled_to_time_interval(five_47, 5))

        twenty_three_59 = calendar.replace(
            hour=23, minute=59, second=0, microsecond=0
        )
        tomorrow_midnight = (calendar.replace(
            hour=23, minute=59, second=0, microsecond=0
        ) + timedelta(minutes=1))
        self.assertEqual(tomorrow_midnight,
                         date_ceiled_to_time_interval(twenty_three_59, 5))

    """ Tests for date_floored_to_time_interval """
    def test_date_floored_to_interval(self):
        calendar = datetime.now()
        five_01 = calendar.replace(hour=5, minute=0, second=1, microsecond=0)
        five = calendar.replace(hour=5, minute=0, second=0, microsecond=0)
        self.assertEqual(five, date_floored_to_time_interval(five_01, 5))

        five_59 = calendar.replace(hour=5, minute=59, second=0, microsecond=0)
        self.assertEqual(five, date_floored_to_time_interval(five_59, 60))

        five_55 = calendar.replace(hour=5, minute=55, second=0, microsecond=0)
        self.assertEqual(five_55, date_floored_to_time_interval(five_59, 5))

        self.assertEqual(five, date_floored_to_time_interval(five, 5))
        self.assertEqual(five_01, date_floored_to_time_interval(five_01, 0))

    """ Tests for time_interval_since_reference_date """
    def test_time_interval_since_reference_date(self):
        self.assertEqual(0, time_interval_since_reference_date(REF_DATE))

        self.assertEqual(371, time_interval_since_reference_date(
            REF_DATE + timedelta(seconds=371)))
        self.assertEqual(12345, time_interval_since_reference_date(
            REF_DATE + timedelta(seconds=12345)))
        self.assertEqual(200, time_interval_since_reference_date(
            REF_DATE + timedelta(seconds=-200)))
        self.assertEqual(86400, time_interval_since_reference_date(
            REF_DATE + timedelta(seconds=-86400)))
        self.assertEqual(86400, time_interval_since_reference_date(
            REF_DATE + timedelta(seconds=86400)))

    def test_time_interval_since(self):
        date = datetime.now()
        self.assertEqual(0, time_interval_since(date, date))

        self.assertEqual(-371,
                         time_interval_since(date, date +
                                             timedelta(seconds=371)))
        self.assertEqual(123456, time_interval_since(
            date, date + timedelta(seconds=-123456)))
        self.assertEqual(-200,
                         time_interval_since(date, date +
                                             timedelta(seconds=200)))
        self.assertEqual(200, time_interval_since(
            date, date + timedelta(seconds=-200)))
        self.assertEqual(86400, time_interval_since(
            date, date + timedelta(seconds=-86400)))
        self.assertEqual(-86400,
                         time_interval_since(date, date +
                                             timedelta(seconds=86400)))


if __name__ == '__main__':
    unittest.main()
