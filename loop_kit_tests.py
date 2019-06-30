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


def load_fixture(resource_name, extension):
    """ Load file given name and extension

    Arguments:
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

    Arguments:
    resource_name -- name of file without the extension
    extension -- ending of file (ex: ".json")

    Output:
    path to file
    """
    search_dir = os.path.dirname(__file__)
    for root, dirs, files in os.walk(search_dir):  # pylint: disable=W0612
        for name in files:
            (base, ext) = os.path.splitext(name)
            if base == resource_name and extension == ext:
                return os.path.join(root, name)

    print("No file found for that key")
    return ""
