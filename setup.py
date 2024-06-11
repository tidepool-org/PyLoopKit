from setuptools import setup, find_packages
import sys


if sys.version_info < (3, 6):
    sys.exit("Sorry, Python < 3.6 is not supported")

with open("README.md", "r") as fh:
    long_description = fh.read()

version_string = "v0.1.0"

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
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
          'numpy>=1.22.0',
          'backports-datetime-fromisoformat==1.0.0',
      ],
    python_requires='>=3.6',
)
