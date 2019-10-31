from setuptools import setup, find_packages
import sys


if sys.version_info < (3, 7):
    sys.exit("Sorry, Python < 3.7 is not supported")

with open("README.md", "r") as fh:
    long_description = fh.read()

version_string = "v0.0.1"

setup(
    name="pyloopkit",
    version=version_string,
    author="Tidepool",
    author_email="ed@tidepool.org",
    description="Python implementation of the Loop algorithm",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tidepool-org/PyLoopKit",
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD-2-Clause',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
          'numpy==1.16.4',
      ],
    python_requires='>=3.6',
)
