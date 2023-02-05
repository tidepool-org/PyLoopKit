# PyLoopKit 
This is a fork of PyLoopkit, which is a set of Python tools for building closed-loop insulin delivery apps (Python port of LoopKit).
The original repository uses Loop issue report data. In this repository the aim is to use Tidepool data instead. Adjustments are mainly made in the file `pyloopkit/pyloop_parser.py`. Please note the [limitations](#limitations) to the current version.

[Link to Tidepool Loop repository version used for algorithm](https://github.com/tidepool-org/Loop/tree/8c1dfdba38fbf6588b07cee995a8b28fcf80ef69)

[Link of Tidepool LoopKit repository version used for algorithm](https://github.com/tidepool-org/LoopKit/tree/57a9f2ba65ae3765ef7baafe66b883e654e08391)

What this repository can do:
- Calculate the blood glucose prediction components (impact from carbohydrates, insulin, momentum and retrospective correction) using the Loop algorithm
- Calculate the blood glucose prediction using the Loop algorithm

# To use this project

## Use the Virtual Environment
In Bash run `source activate py-loop`, or in the Anaconda Prompt
run `conda activate py-loop` to start the environment.

Run `deactivate` to stop the environment.

## Run example script
In Terminal run
`python3 example.py`
in the main directory. 

The example script is the same as the original script, but instead of using Loop issue report, it uses a Tidepool export in Excel format. It uses the last measured glucose value in the data as a reference and calculates the predicted glucose trajectory.

See `pyloopkit/example_files/TidepoolExport.xlsx` for the example data. Therapy settings used for blood glucose prediction can be adjusted in `pyloopkit/example_files/therapy_settings.json`.

## PyLoopKit Instructions
To read about usage instructions, input data requirements, and other important details please review [the documentation](pyloopkit/docs/pyloopkit_documentation.md).

### To recreate the Virtual Environment
1. This environment was developed with Anaconda. You'll need to install [Miniconda](https://conda.io/miniconda.html) or [Anaconda](https://anaconda-installer.readthedocs.io/en/latest/) for your platform.
2. In a terminal, navigate to the directory where the environment.yml 
is located (likely in PyLoopKit/pyloopkit folder).
3. Run `conda env create`; this will download all of the package dependencies
and install them in a virtual environment named py-loop. PLEASE NOTE: this
may take up to 30 minutes to complete.

### To create the PyLoopKit package
If you want to install a version of the PyLoopKit package based on the PyLoopKit on your local machine, run `python3 setup.py install` within your PyLoopKit repo to call the setup script and install the package. You'll likely want to do this within the `py-loop` environment.

### Running the unittests
To run PyLoopKit's unit tests, run `python3 -m unittest discover` within your PyLoopKit repo

# Limiations and Further Plans

<a name="limitations"></a> 
## Limitations 
- Tidepool exports do not include end dates for bolus doses, so this repository assumes that bolus injections are delivered momentarily
- Timezone for the computer is used, not from the dataset
- Therapy settings is assuming you are using mg/dL, there should be a simple way to adjust units used
- Carbohydrate model is by default parabolic (linear in original repository), there should be a simple way to adjust that
- The therapy settings are not read from the collected data and hence do not include overrides
	- Instead, therapy settings are stored in `pyloopkit/example_files/therapy_settings.json`
	- This is in the backlog to be fixed, but is not a bottleneck for exploring how to optimize therapy settings in Loop

## Further Plans 
- Refactoring. The focus until now has been to making it work.
- Possibly implementing support for Nightscout API
- Verify that the predictions are correct in several scenarious
- Implementing a function that takes a datetime/glucose sample as an input and returns predicted values from this reference point
- Implementing a function that takes a datetime/glucose sample as an input and returns measured values from this reference point
- Implementing a function that calculates the forecast evaluation by Damon Bayer [documented here](https://docs.google.com/document/d/14AJ9u2oGJiiJU1cWVDf_rC_WdJc0oOj1uIkXutOovQU/edit)














