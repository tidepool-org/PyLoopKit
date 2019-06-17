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


class HKQuantity:
    """ Constructs a value with amount and unit.

    Attributes:
    unit -- unit of the double_value
    double_value -- amount of whatever you're putting in
    """
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
    """ Load file given name and extension

    Keyword arguments:
    resource_name -- name of file without the extension
    extension -- ending of file (ex: ".json")

    Output:
    contents of file
    """
    path = find_full_path(resource_name, extension)
    return json.load(open(path))


# this will return the FIRST instance of the file
def find_full_path(resource_name, extension):
    """ Find file path, given name and extension

    Keyword arguments:
    resource_name -- name of file without the extension
    extension -- ending of file (ex: ".json")

    Output:
    path to file
    """
    search_dir = os.path.dirname(__file__)
    for root, dirs, files in os.walk(search_dir):
        for name in files:
            (base, ext) = os.path.splitext(name)
            if base == resource_name and extension == ext:
                return os.path.join(root, name)
    print("No file found for that key")
    return ""
