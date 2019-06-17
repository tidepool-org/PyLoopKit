#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 16 15:41:18 2019

@author: annaquinlan
"""
from datetime import datetime, timedelta
from date import (date_floored_to_time_interval, date_ceiled_to_time_interval,
                  time_interval_since_reference_date, time_interval_since)


"""
  Checks if two times are equal
- input: two datetime objects
- output: string stating that test is passed or failed
"""


def is_test_passed(time_1, time_2):
    if time_1 == time_2:
        return "Test passed"
    else:
        return "Test failed;", time_1.strftime('%m/%d/%y %H:%M:%S.%f'),\
               "!=", time_2.strftime('%m/%d/%y %H:%M:%S.%f')


"""
  Checks if two numbers are equal
- input: two datetime objects
- output: string stating that test is passed or failed
"""


def is_test_passed_nums(num_1, num_2):
    if num_1 == num_2:
        return "Test passed"
    else:
        return "Test failed;", num_1, "!=", num_2


"""
  Tests for date_ceiled_to_time_interval
"""


def test_date_ceiled_to_interval():
    calendar = datetime.now()
    five_01 = calendar.replace(hour=5, minute=0, second=1, microsecond=0)
    five_05 = calendar.replace(hour=5, minute=5, second=0, microsecond=0)
    print(is_test_passed(five_05, date_ceiled_to_time_interval(five_01, 5)))
    print(is_test_passed(five_01, date_ceiled_to_time_interval(five_01, 0)))

    six = calendar.replace(hour=6, minute=0, second=0, microsecond=0)
    print(is_test_passed(six, date_ceiled_to_time_interval(five_01, 60)))

    print(is_test_passed(five_05, date_ceiled_to_time_interval(five_05, 5)))

    five_47 = calendar.replace(hour=5, minute=47, second=58, microsecond=0)
    five_50 = calendar.replace(hour=5, minute=50, second=0, microsecond=0)
    print(is_test_passed(five_50, date_ceiled_to_time_interval(five_47, 5)))

    twenty_three_59 = calendar.replace(hour=23, minute=59, second=0,
                                       microsecond=0)
    tomorrow_midnight = (calendar.replace(hour=23, minute=59, second=0,
                                          microsecond=0) +
                         timedelta(minutes=1))
    print(is_test_passed(tomorrow_midnight,
                         date_ceiled_to_time_interval(twenty_three_59, 5)),
          "\n")


"""
  Tests for date_floored_to_time_interval
"""


def test_date_floored_to_interval():
    calendar = datetime.now()
    five_01 = calendar.replace(hour=5, minute=0, second=1, microsecond=0)
    five = calendar.replace(hour=5, minute=0, second=0, microsecond=0)
    print(is_test_passed(five, date_floored_to_time_interval(five_01, 5)))

    five_59 = calendar.replace(hour=5, minute=59, second=0, microsecond=0)
    print(is_test_passed(five, date_floored_to_time_interval(five_59, 60)))

    five_55 = calendar.replace(hour=5, minute=55, second=0, microsecond=0)
    print(is_test_passed(five_55, date_floored_to_time_interval(five_59, 5)))

    print(is_test_passed(five, date_floored_to_time_interval(five, 5)))
    print(is_test_passed(five_01, date_floored_to_time_interval(five_01, 0)),
          "\n")

"""
  Tests for time_interval_since_reference_date
"""


def test_time_interval_since_reference_date():
    ref_date = datetime(2001, 1, 1, 0, 0, 0)
    print(is_test_passed_nums(0, time_interval_since_reference_date(ref_date)))
    
    print(is_test_passed_nums(371,
                              time_interval_since_reference_date(ref_date +
                                                                 timedelta(seconds=371))))
    print(is_test_passed_nums(12345,
                              time_interval_since_reference_date(ref_date +
                                                                 timedelta(seconds=12345))))
    print(is_test_passed_nums(200,
                              time_interval_since_reference_date(ref_date +
                                                                 timedelta(seconds=-200))))
    print(is_test_passed_nums(86400,
                              time_interval_since_reference_date(ref_date +
                                                                 timedelta(seconds=-86400))))
    print(is_test_passed_nums(86400,
                              time_interval_since_reference_date(ref_date +
                                                                 timedelta(seconds=86400)))
          , "\n")

def test_time_interval_since():
    date = datetime.now()
    print(is_test_passed_nums(0, time_interval_since(date, date)))
    
    print(is_test_passed_nums(-371,
                              time_interval_since(date, date +
                                                  timedelta(seconds=371))))
    print(is_test_passed_nums(123456,
                              time_interval_since(date, date +
                                                  timedelta(seconds=-123456))))
    print(is_test_passed_nums(-200,
                              time_interval_since(date, date +
                                                  timedelta(seconds=200))))

    print(is_test_passed_nums(200,
                              time_interval_since(date, date +
                                                  timedelta(seconds=-200))))
    print(is_test_passed_nums(86400,
                              time_interval_since(date, date +
                                                  timedelta(seconds=-86400))))
    print(is_test_passed_nums(-86400,
                              time_interval_since(date, date +
                                                  timedelta(seconds=86400))),
          "\n")


test_date_ceiled_to_interval()
test_date_floored_to_interval()
test_time_interval_since_reference_date()
test_time_interval_since()
