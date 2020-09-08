# PyLoopKit Docs

Welcome to the documentation for PyLoopKit. This document contains instructions to help get you oriented to the project, and includes details on running the Loop Algorithm in Python. The project was started by Anna Quinlan in the summer of 2019; if you have any questions please reach out to [Ed Nykaza](mailto:ed@tidepool.org).

# Important Notes



*   PyLoopKit was built using Python 3.7.3; there is an environment file in the project that can be used with Anaconda or Miniconda to recreate the virtual environment.
*   PyLoopKit does not support glucose values that are in mmol/L; they must be converted to mg/dL before usage (conversion can be done by multiplying by 18.01559)
*   Though PyLoopKit is able to work with dates with a consistent time zone, it has not been tested when there are time zone changes within the data itself
*   PyLoopKit uses the datetime objects to store dates and times. Dates with timezones must either have the correct timezone (ex: 2019-08-12 01:28:19 -0700), or be in UTC and have a constant offset (ex: 2019-08-12 01:28:19 +0000, with an offset of -25200 seconds)
*   In order to prepare for vectorization, PyLoopKit uses index-matched lists to store data, instead of objects like Loop
    *   Example: if `glucose_dates = [14:00, 14:05, 14:10]` and `glucose_values = [105, 102, 104]`, then that would mean a BG measurement of 105 mg/dL at 2:00 PM, 102 mg/dL at 2:05 PM, and 104 mg/dL at 2:10 PM
*   There is no support for integral retrospective correction (only retrospective correction); these correction methods, though they have similar names, utilize different methods to compute the correction and as such will return different predictions.
*   If _(and only if)_ you are running PyLoopKit **using data from a Loop issue report**, predicted glucose values (and the recommended basals/bolus) **will likely be slightly off.** This is because the issue report does not contain the full insulin history.
    *   To correctly calculate counteraction effects at a point in time, the past duration of insulin action (DIA)-worth of insulin is required; Loop uses 24 hours of counteraction effects to calculate carbohydrate effects and retrospective correction effects.
    *   However, there are only 24 hours of dose history in a report, meaning that the first DIA-worth of counteraction effects will be incorrect because not all insulin active at that time was accounted for. This will affect three of the four effects that are output by the issue report (insulin, carb and retrospective correction effects). The insulin effects will still have the same momentary effects, but since some initial IOB was unaccounted for, the value of the overall effect will differ.
*   If, having read the caution above, you still would like to use an issue report with PyLoopKit, the issue report must _first_ be run through [the issue report parser](https://github.com/tidepool-org/data-analytics/tree/master/projects/parsers) in the [Tidepool data analytics repository](https://github.com/tidepool-org/data-analytics) to convert it from Markdown to json
*   As you read through this doc <strong><code>bold()</code></strong> is used for functions.


# 


# Getting Oriented

_Functions to Run the Loop Algorithm_



*   If you are passing in data from an issue report, you can use the function <strong><code>parse_report_and_run()</code></strong> in <code>pyloop_parser.py</code>. This function expects the input file to have been generated through [the issue report parser](https://github.com/tidepool-org/data-analytics/tree/master/projects/parsers) in the [Tidepool data analytics repository](https://github.com/tidepool-org/data-analytics).
*   If passing data from a previous run, or data that you have prepared to be in the format specified in “Input Data Requirements”, pass it into <strong><code>update()</code></strong> in <code>loop_data_manager.py</code>

<em>Tests</em>



*   PyLoopKit has tests (using `unittests`) for all major functions
*   The tests are located in the test folder; fixtures are located in the fixtures folder
*   To run tests, navigate to the test folder and run `python3 -m unittest -v`
*   PyLoopKit has manually been tested with seven issue reports from actual Loopers, and around ten issue reports generated with a simulator pump and CGM
    *   There are also four automatic tests that utilize issue reports and validate the accuracy of the glucose prediction and recommendations
*   This project has been primarily tested using issue reports _without_ overrides, though there is support for overrides in the PyLoopKit issue report parser.

_How Effects Used for Glucose Predictions Are Calculated_



1. Momentum effects: 
<strong><code>get_recent_momentum_effects()</code></strong> in <code>glucose_store.py</code>
    1. Filters the glucose data so that it is within <code>momentum_data_interval</code> minutes
    2. Calls <strong><code>linear_momentum_effect() </code></strong>in <code>glucose_math.py</code> to calculate the glucose momentum effect
        1. Checks that the glucose values are valid, with only one provenance (<strong><code>has_single_provenance()</code></strong>), no CGM calibration values (<strong><code>is_calibrated()</code></strong>), and BG values that are continuous  (<strong><code>is_continuous()</code></strong>)
        2. Does a linear regression on the BG values with <strong><code>linear_regression()</code></strong>, then uses the slope to project momentum effect for each value, proportional to the time since the starting date
            1. Momentum effect <strong><em>cannot</em></strong> be negative
2. Insulin effects: <strong><code>get_glucose_effects()</code></strong> in <code>dose_store.py</code>
    1. Filters dose data so that the data starts at start time minus DIA
    2. Reconciles the data, trimming overlapping temporary basal rates (temp basals) and adding resumes for suspends (if necessary) using <strong><code>reconciled()</code></strong> in <code>insulin_math.py</code>
    3. Sorts the data, since <strong><code>reconciled()</code></strong> often makes the doses slightly out of order
    4. Annotates the data with the scheduled basal rate during the dose using <strong><code>annotated()</code></strong> in <code>insulin_math.py</code>; boluses have a scheduled basal rate of 0 U/hr.
    5. Trims doses to the start of the interval (start time - DIA)
    6. Gets insulin effects using <strong><code>glucose_effects() </code></strong>in <code>insulin_math.py</code>
        1. Determines what the start and end times for the effects should be using <strong><code>simulation_date_range_for_samples()</code></strong>
        2. Iterates from the start to the end in <code>delta</code>-long intervals (where delta is typically set to 5 minutes), finding the partial insulin effect for each dose at a given <code>date</code> using <strong><code>glucose_effect()</code></strong>
            1. Determines the percentage of the dose that has been used up before <code>date</code> if the dose is shorter than 1.05 * <code>delta</code> (typically a bolus or very short temp basal) with the computation 1 - percent_effect_remaining
            2. Determines the percentage of the dose that has been used up before <code>date</code> if the dose is shorter than 1.05 * <code>delta</code> (typically temp basal) with the computation 1 - <strong><code>continuous_delivery_glucose_effect()</code></strong>
            3. Calculates the Units of insulin (net of any scheduled basal rates) in the dose with<code> <strong>net_basal_units</strong>()</code>, then multiplies by negative insulin <code>sensitivity</code> and the percentage of used dose to calculate the partial effect
    7. Filters effects so they start at the start time
3. Carb effects: <strong><code>get_carb_glucose_effects()</code></strong> in <code>carb_store.py</code>
    1. Filters the carb data so it starts at start time minus <code>maximum_absorption_time_interval</code> (the slowest absorption time * 2)
    2. If counteraction effects are provided, calculates the absorption dynamically using <strong><code>map_()</code></strong> and <strong><code>dynamic_glucose_effects()</code></strong>
        1. <strong><code>map_()</code></strong> generates a timeline of absorption and absorption statistics. It calculates the carb absorption using positive counteraction effects, then if there are multiple active carb entries, splits the absorption proportionally based on the minimum expected absorption rates.
        2. <strong><code>dynamic_glucose_effects() </code></strong>determines what the start and end times for the effects should be using <strong><code>simulation_date_range()</code></strong>, then iterates from start to the end in <code>delta</code>-long intervals, suming the partial carb effects at that <code>date</code> for each entry using <strong><code>dynamic_absorbed_carbs()</code></strong> in carb_status.py
            1. If there is no absorption information for an entry, effects are calculated using<code> <strong>absorbed_carbs</strong>()</code> in <code>carb_math.py</code>, which is a parabolic model
            2. If less than the minimum expected absorption is observed, the absorbed carbs are calculated linearly with <strong><code>linearly_absorbed_carbs()</code></strong> in <code>carb_math.py</code> to ensure they eventually absorb
    3. If counteraction effects are not provided (which is <em>very</em> rare), it calculates the absorption using <strong><code>carb_glucose_effects</code></strong>(), which uses a parabolic model to generate the timeline.
4. Retrospective correction (if enabled): <strong><code>update_retrospective_glucose_effect()</code></strong> in <code>loop_data_manager.py</code>
    1. “Subtracts” the carb effects from the counteraction effects to determine discrepancies over <code>delta</code>-minute intervals using <strong><code>subtracting()</code></strong> in <code>loop_math.py</code>
    2. Sums those discrepancies over time using <strong><code>combined_sums()</code></strong> in <code>loop_math.py</code>
    3. Calculates the average velocity of the retrospective discrepancies, then decays that effect linearly with <strong><code>decay_effect()</code></strong> in <code>loop_math.py</code>, using the most recent glucose measurement as the starting point


# 


# Input Data Requirements

If using an issue report, you can skip this section; this will be handled by the PyLoopKit issue report parser. **All the input data must be contained in one dictionary with the necessary keys. **PyLoopKit uses index-matched lists to store data, so when discussing the data properties and requirements, it is assumed that these will be _lists_ of the values (unless otherwise noted) that are matched index-wise. This information is also contained in the doc-string of **update**() in loop_data_manager.py

_Glucose Data_



*   Required Lists
    *   “glucose_dates”
        *   the time of the BG measurement as a datetime object
    *   "glucose_values" (BG value)
        *   must be in mg/dL
        *   Example: 150

_Insulin Data_



*   PyLoopKit will automatically trim overlapping doses and add resumes for suspends
*   Required Lists
    *   “dose_types”
        *   DoseType enums (the class is contained in `dose.py`)
            *   When initializing, string must be either “Bolus”, “TempBasal”, “BasalProfileStart”/ “Basal”, or “PumpSuspend”/”Suspend” (case-insensitive)
        *   the input validation function will issue a warning if there are types that are not these values
    *   “dose_start_times”
        *   time the dose started at as a datetime object
    *   “dose_end_times”
        *   time dose ended at as a datetime object
        *   If dose is type “Bolus”, the end time the time the pump finished delivery of the bolus
    *   “dose_values”
        *   **Units of insulin** in dose (if a bolus) **or the basal rate in U/hr** (if a basal)
            *   For basals, this is *not* a net basal rate; it’s the basal rate that the pump was set to, or that Loop set the pump to
        *   Bolus example: 1.5
        *   Basal example: 0.2

_Carbohydrate Data_



*   Required Lists
    *   “carb_dates”
        *   time carbohydrates were consumed at (ISO-formatted date)
        *   Example: "2015-07-13T12:02:37"
    *   “carb_values”
        *   grams of carbohydrates consumed
        *   Example: 20
    *   “carb_absorption_times”
        *   estimated absorption time in minutes
            *   this is the “lollipop, taco, pizza” option in Loop
        *   if no absorption time is specified, defaults to medium, which is 180 minutes (3 hours)
            *   Pass a list with `None` values if not specifying absorption time
        *   Example: 120

_Settings Data_



*   key: “settings_dictionary”
*   **_<span style="text-decoration:underline;">dictionary</span>_** of various settings
*   Required Keys
    *   “insulin_model” (insulin model)
        *   list containing insulin model information
        *   model is either Walsh or exponential; this typing can be inferred from the length of the list
        *   if Walsh:
            *   structure = [DIA (in **hours**)]
            *   Example: [4]
        *   if exponential:
            *   structure = [DIA (in **minutes**), peak (in **minutes**)]
            *   Child model has a peak at 65 mins, adult model has peak at 75 mins
            *   Example for adult: [240, 75]
            *   Example for child: [240, 65]
    *   “max_basal_rate”
        *   the maximum basal rate that Loop will deliver (in Units/hr)
        *   Example: 4
    *   “max_bolus” 
        *   the maximum bolus that Loop will recommend (in Units)
        *   Example: 10
    *   “suspend_threshold”
        *   glucose value (mg/dL) on the prediction curve at which Loop will set a zero-temp and not recommend any boluses
        *   If the suspend_thresold is `None`, PyLoopKit defaults to the lower value of the correction range at the time the “loop” is being run at, which mirrors the behavior of Loop
        *   Example: 70
    *   “default_absorption_times”
        *   list of absorption times (minutes) to default to if there is no specified absorption time for a carb entry
        *   format: [default **fast** absorption time, default **medium_ _**absorption time, default **slow** absorption time]
        *   Loop defaults to [120, 180, 240]
*   Optional Keys
    *   “insulin_delay”
        *   minutes to delay the insulin absorption
        *   PyLoopKit and Loop default to 10 (minutes)
    *   “rate_rounder” (rounding increment)
        *   the interval to round basals & bolus (this is pump-specific)
            *   Some Medtronic pumps can dose in 0.025 U increments, versus Omnipod doses in 0.05 U increments
        *   If not present, PyLoopKit does not round dose values
        *   Example: 0.05
            *   This would round a temp basal of 0.266 U/hr to 0.25 U/hr, or a temp basal of 0.271 U/hr to 0.30 U/hr
    *   “retrospective_correction_enabled”
        *   Boolean on whether to enable retrospective correction
        *   PyLoopKit and Loop default to False
        *   Example: False (to disable)
    *   “dynamic_carb_absorption_enabled”
        *   Boolean on whether to allow carb effects to be calculated dynamically
        *   PyLoopKit and Loop default to True
    *   “retrospective_correction_grouping_interval”
        *   Interval (minutes) over which to aggregate changes in glucose for retrospective correction
        *   PyLoopKit and Loop default to 30
    *   "retrospective_correction_integration_interval"
        *   Interval (minutes) of the time over which to integrate the retrospective correction effects
        *   PyLoopKit and Loop default to 30
    *   "recency_interval"
        *   how recent the glucose measurements must be in order to calculate retrospective correction effects (minutes)
        *   PyLoopKit and Loop default to 15
    *   “momentum_data_interval”
        *   interval (minutes) of recent BG measurements to use to calculate the momentum effect
        *   PyLoopKit and Loop default to 15 (minutes)

_Insulin Sensitivity Schedule_



*   Required Lists
    *   "sensitivity_ratio_start_times"
        *   time the sensitivity value starts being used (datetime **time** object)
        *   Example: time(0, 0, 0)
    *   "sensitivity_ratio_end_times"
        *   time the sensitivity value stops being used (datetime **time** object)
        *   Example: time(23, 59, 59)
        *   The end time can be the same as the start time if there is one ratio for the whole day
    *   "sensitivity_ratio_values"
        *   insulin sensitivity factor (ISF) in mg/dL per Unit of insulin
            *   amount one Unit will drop blood glucose levels
        *   Example: 40

_Carb Ratio Schedule_



*   Required Lists
    *   "carb_ratio_start_times"
        *   time the carb ratio starts being used (datetime **time** object)
        *   Example: time(0, 0, 0)
    *   "carb_ratio_values"
        *   carb ratio in grams of carbohydrates per Unit of insulin
        *   Example: 10

_Basal Schedule_



*   Required Lists
    *   "basal_rate_start_times"
        *   time the basal starts being used (datetime **time** object)
        *   Example: time(0, 0, 0)
    *   "basal_rate_values"
        *   the length of time the basal runs for (in minutes)
        *   Example: 600
    *   "basal_rate_minutes"
        *   the infusion rate in U/hour
        *   Example: 0.85

_Correction Range Schedule_



*   Required Lists
    *   "target_range_start_times"
        *   time the target range starts being used (datetime **time** object)
        *   Example: time(0, 0, 0)
    *   "target_range_end_times"
        *   time the target range stops being used (datetime **time** object)
        *   Example: time(23, 59, 59)
        *   The end time can be the same as the start time if there is one range for the whole day
    *   "target_range_minimum_values"
        *   minimum value for target range (mg/dL)
        *   Example: 80
    *   "target_range_maximum_values"
        *   maximum value for target range (mg/dL)
        *   Example: 100

_Last Temporary Basal Rate_



*   key: "last_temporary_basal"
*   list of information about the last temporary basal
*   Form: [type of dose, start time for basal, end time for basal, basal rate in U/hr]
    *   Type must be DoseType.tempbasal or DoseType.basal
*   If not present, PyLoopKit defaults to an empty list

_Time to Calculate At_



*   key: "time_to_calculate_at"
*   the time to assume as the “now” time, which is also the time to recommend the temporary basal and bolus at (datetime object)


# 


# Usage

_Installing the Virtual Environment_



1. The PyLoopKit environment was developed with Anaconda. You'll need to install [Miniconda](https://conda.io/miniconda.html) or [Anaconda](https://anaconda-installer.readthedocs.io/en/latest/) for your platform.
2. In a terminal, navigate to the directory where the environment.yml is located (likely the PyLoopKit/pyloopkit folder).
3. Run `conda env create`; this will download all of the package dependencies and install them in a virtual environment named py-loop. PLEASE NOTE: this may take up to 30 minutes to complete.

_Using the Virtual Environment_



*   In Terminal run `source activate py-loop`, or in the Anaconda Prompt run `conda activate py-loop` to start the environment.
*   Run `deactivate` to stop the environment.

_Using the Examples_



*   Example input and output files can be found in the example_files folder
*   Run `example.py` (located in the main directory) to run an example input file through the algorithm and generate graphs of the calculated data
    *   File options: 
        *   `example_issue_report_1.json`
            *   Issue report with an exponential **_adult_** insulin curve
        *   `example_issue_report_2.json`
            *   Issue report with an exponential **_child_** insulin curve
        *   `example_issue_report_3.json`
            *   Issue report with retrospective correction effects enabled
        *   `example_issue_report_4.json`
            *   Issue report with Walsh insulin model
        *   `example_from_previous_run.json` 
            *   input dictionary that was saved from the output of a previous run of <strong><code>update()</code></strong>
    *   There is code in <code>example.py</code> to run any of these files; uncomment the file you want to use
    *   An output json file will be generated and saved

<em>Importing from an Issue Report</em>



*   The issue report must be have already been parsed into json format with the parser found in [Tidepool’s data-science repository](https://github.com/tidepool-org/data-analytics)
*   <strong><code>parse_report_and_run()</code></strong> in <code>pyloop_parser.py</code> is the function that can automatically take this json issue report, extract the data into a usable format, then run it through the algorithm and give recommendations
*   The path and file name are required
    *   For Mac, an example would be 

        ```
        path = "/Users/jamesjellyfish/Downloads"
        file_name = "issue_report.json"
        ```


    *   For Windows, an example would be

        ```
        path = "c:\Users\jamesjellyfish\Downloads"
        file_name = "issue_report.json"
        ```


    *   Sample call: **<code>parse_report_and_run(path, file_name)</code></strong>

<em>Directly Passing Data</em>



*   <strong><code>update()</code></strong> in <code>loop_data_manager.py</code> can take the input dictionary, run it through the algorithm, and return an output dictionary
    *   <strong><code>update()</code></strong> takes one input dictionary and extracts all the necessary information, provided the keys are the same as are specified in “Input Data Requirements”

<em>Input Validation in PyLoopKit</em>



*   In order to flag unreasonable inputs, PyLoopKit uses the functions in `input_validation_tools.py`
*   Two types of notices: warnings and errors
    *   Warnings do not stop PyLoopKit from running; errors **_do_** stop the run
    *   Warnings use the Loop guardrail values (see [this document](https://docs.google.com/document/d/1G8Fvwib2bRd_XcN_Ph34qqoEQfO1ROb4IfM1bGS9obU/edit?usp=sharing) for more information)
    *   Errors are for values that are highly unreasonable
        *   Example: a negative DIA
*   If you believe that these thresholds are not appropriate for your dataset, please change the relevant values.

_Interpreting the Output_



*   PyLoopKit returns a dictionary containing each calculated effect, the glucose prediction, the recommendation for a temp basal and/or bolus, and a dictionary of the input data into the algorithm
    *   For each effect or glucose prediction, there are two index-matched lists: one for dates, and one for effect values
*   Effect Values
    *   Momentum, insulin, carb, and retrospective correction effects are in **mg/dL**
        *   You can calculate the change in mg/dL/min with simple arithmetic; `(value_2 - value_1) / (time_2 - time_1)`
    *   Counteraction effects are in **mg/dL/minute**
*   Glucose prediction
    *   Also in **mg/dL**
    *   Includes all the effects that were calculated
*   Recommended temporary basal rate
    *   List in format [temporary basal rate, minutes to run the temp for]
        *   [0.475, 30] would mean a rate of 0.475 U/hr for 30 minutes
    *   If there is no recommendation, Loop is opting to continue the current temp basal (or the scheduled basal if no temp is running)
        *   This occurs a lot with issue reports, because the “last temporary basal” is often the temp basal that was set with the most recent run of the loop
    *   If the recommendation has a duration of 0 minutes, Loop is opting to cancel the current temp and return to the scheduled basal rate
        *   [0.5, 0] would be a cancel command because the recommended temp of 0.5 U/hr is the same as the scheduled basal rate
*   Recommended bolus
    *   List in format [units of insulin, pending insulin, recommendation notice]
        *   [0, 0.3, ["glucoseBelowSuspendThreshold", 56.1]] would mean there are 0.3 U of pending insulin, and Loop is recommending a bolus of 0 U because a point on the predicted glucose graph is 56.1 mg/dL, which is below the suspend threshold
        *   [0.5, 0, None] would mean there are 0 U of pending insulin, and Loop is recommending a bolus of 0.5 U
    *   Pending insulin is the insulin that is planned but not yet been delivered
        *   Composed of pending basal amount + pending bolus amount
            *   Pending basal is defined as the net units that have yet to be delivered by the currently running temp
            *   **Pending boluses are not reflected in issue reports**, thus the **recommended bolus may differ** if using an issue report and there was a pending bolus
    *   Bolus recommendation notices are the warnings displayed above the bolus screen in Loop if the prediction is either below target or below the suspend threshold
*   Dictionary of input data
    *   Key: “input_data”
    *   Can be used to re-run the algorithm in the future if desired
