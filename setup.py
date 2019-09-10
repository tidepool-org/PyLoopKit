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


# %% START OF SETUP
with open("README.md", "r") as fh:
    long_description = fh.read()

version_string = "v0.0.1"

setuptools.setup(
    name="pyLoopKit",
    version=version_string,
    author="Ed Nykaza",
    author_email="ed@tidepool.org",
    description="pyLoopKit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tidepool-org/PyLoopKit",
    packages=setuptools.find_packages(),
    download_url=(
        'https://github.com/tidepool-org/PyLoopKit/tarball/' + version_string
    ),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD-2-Clause',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
          'numpy==1.16.4',
          'pandas==0.24.2',
          'tensorflow==2.0.0-beta1',
          'plotly==4.1.0',
          'matplotlib==3.1.1',
      ],
)


# %% CLEAN UP
# remove the excess files if package is installed with pip from github
# TODO: make tidals its own repository under tidepool_org
# once tidals becomes its own github repository, then this step will no longer be necessary
# TODO: publish tidals as a PyPi pacakge

files = glob.glob(os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "*")))

hidFiles = glob.glob(os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", ".*")))

allFiles = files + hidFiles

# if loaded from github with pip in environmental.yml, then when it will
# create a source file (src) and clone the entire data-analytics repo
"""
for i in allFiles:
    # make sure you are in the src/tidals/ directory
    if "src" in i.split(sep=os.sep)[-3]:
        # delete all BUT files in tidals package
        if "tidepool-analysis-tools" not in i:
            if os.path.isdir(i):
                shutil.rmtree(i)
            else:
                os.remove(i)
"""