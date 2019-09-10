#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
description: setup script for the tidals package
created: 2018-10-01
author: Ed Nykaza
license: BSD-2-Clause
Parts of this file were taken from
https://packaging.python.org/tutorials/packaging-projects/
"""

# %% REQUIRED LIBRARIES
import setuptools
import os
import glob
import shutil
import sys


if sys.version_info < (3, 7):
    sys.exit("Sorry, Python < 3.7 is not supported")

# %% START OF SETUP
with open("README.md", "r") as fh:
    long_description = fh.read()

version_string = "v0.0.1"

setuptools.setup(
    name="pyloopkit",
    version=version_string,
    author="Ed Nykaza",
    author_email="ed@tidepool.org",
    description="pyLoopKit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tidepool-org/PyLoopKit",
    packages=setuptools.find_packages(),
    include_package_data=True,
    download_url=(
        'https://github.com/tidepool-org/PyLoopKit/tarball/' + version_string
    ),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD-2-Clause',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
          'numpy==1.16.4',
          'pandas==0.24.2',
          'tensorflow==2.0.0-beta1',
          'plotly==4.1.0',
          'matplotlib==3.1.1',
      ],
)