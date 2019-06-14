#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 09:25:37 2019

@author: annaquinlan

Github URL: https://github.com/tidepool-org/LoopKit/blob/
57a9f2ba65ae3765ef7baafe66b883e654e08391/LoopKitTests/LoopKitTests.swift
"""
import json
import os
from datetime import datetime


class HKQuantity:
    def __init__(self, unit, double_value):
        self.unit = unit
        self.double_value = double_value

    def __lt__(self, other):
        self_value = self.double_value
        other_value = other.double_value
        return self_value < other_value

    def __gt__(self, other):
        self_value = self.double_value
        other_value = other.double_value
        return self_value > other_value

    def __eq__(self, other):
        self_value = self.double_value
        other_value = other.double_value
        return self_value == other_value


def load_fixture(resource_name, extension):
    path = find_full_path(resource_name, extension)
    return json.load(open(path))


# this will return the FIRST instance of the file
def find_full_path(resource_name, extension):
    search_dir = os.path.dirname(__file__)
    for root, dirs, files in os.walk(search_dir):
        for name in files:
            (base, ext) = os.path.splitext(name)
            if base == resource_name and extension == ext:
                return os.path.join(root, name)
    print("No file found for that key")
    return ""


# converts string to datetime object in the ISO 8601 format
def date_formatter(date_string):
    try:
        iso_date = datetime.strptime(date_string,
                                     "%Y-%m-%dT%H:%M:%S")
    except Exception as e:
        print(e)
        iso_date = datetime.strptime(date_string,
                                     "%Y-%m-%dT%H:%M:%S%z")
    return iso_date
