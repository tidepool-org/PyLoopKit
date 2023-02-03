#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C0200, C0103, R0912, R0913, R0914, R0915
import json
import os
import warnings
import pandas as pd

from datetime import datetime, time, timedelta
import numpy

from pyloopkit.dose import DoseType
from pyloopkit.loop_data_manager import update
from pyloopkit.loop_math import sort_dose_lists

# %% Functions to get various data from an issue report
def get_glucose_data(dataframe_glucose, offset=0):
        """ Load glucose values from an issue report cached_glucose dictionary

        Arguments:
        df -- the dataframe of the CGM measurements in a Tidepool export 

        Output:
        2 lists in (date, glucose_value) format
        """

        dates = [
                datetime.strptime(
                        str(date).split('.')[0],
                        "%Y-%m-%d %H:%M:%S"
                ) + timedelta(seconds=offset)
                for date in dataframe_glucose['Local Time']
        ]

        glucose_values = [value for value in dataframe_glucose['Value']]

        assert len(dates) == len(glucose_values),\
                "expected output shape to match"

        return (dates, glucose_values)


def convert_to_correct_units(type_, start, end, value):
        """ Take a dose and convert it into the appropriate unit
                (either U or U/hr)
        """
        if type_ == DoseType.bolus:
            return value
        elif (start - end).total_seconds() == 0:
            return value
        else: 
            return value / ((end - start).total_seconds()/60/60)


def get_insulin_data(
        dataframe_bolus, dataframe_basal,
        offset=0, convert_to_units=False, entry_to_add=None,
        now_time=None):
    """ Load doses from an issue report cached_doses
        or normalized_insulin_doses dictionary

    Arguments:
    data -- dictionary containing cached dose information
    offset -- the offset from UTC in seconds
    convert_to_units -- convert from dose amounts to doses with the correct
                        units (so U for boluses and U/hr for basals)
    entry_to_add -- the last entry to add; this is normally used when getting
                    data from the "get_normalized_pump_event_dose" dictionary,
                    as it sometimes lacks the last insulin dose. This function
                    assumes that if it is a basal, it will need to be converted
                    to U/hr.
    now_time -- the time to run the loop at ("datetime.now")

    Output:
    4 lists in (dose_type (DoseType enum), start_dates, end_dates,
                values (in units/insulin)) format
    """
    dose_types = [
        DoseType.from_str(
            "bolus"
        ) for _ in range(dataframe_bolus.shape[0])
    ]
    for val in dataframe_basal['Delivery Type']:
        if val == 'temp':
            dose_types.append(DoseType.from_str('tempbasal'))
        else:
            dose_types.append(DoseType.from_str('basal'))

    start_dates = [
        datetime.strptime(
            str(date).split('.')[0],
            "%Y-%m-%d %H:%M:%S"
        ) + timedelta(seconds=offset)
        for date in dataframe_bolus['Local Time']
    ]
    # Tidepool export does unfortunately not add end dates to bolus doses
    end_dates = start_dates.copy()
    
    for date in dataframe_basal['Local Time']:
        start_dates.append(
            datetime.strptime(
            str(date).split('.')[0],
            "%Y-%m-%d %H:%M:%S"
            ) + timedelta(seconds=offset)
            )

    end_dates_basal = dataframe_basal.apply(lambda x: x['Local Time'] + pd.Timedelta(x["Duration (mins)"], 'm'), axis=1)
    
    for date in end_dates_basal:
        end_dates.append(
            datetime.strptime(
            str(date).split('.')[0],
            "%Y-%m-%d %H:%M:%S"
            ) + timedelta(seconds=offset) 
            )

    values = [
        val for val in dataframe_bolus['Normal']
        ]
    
    # TO DO: INSULIN DOSES THAT ARE ZERO SHOULD NOT BE INCLUDED AT ALL

    for val in dataframe_basal['Rate']:
        values.append(val)

    # Convert from U/h to U for basal rates
    for i in range(len(dataframe_bolus), len(dataframe_bolus) + len(dataframe_basal)):
        basal_in_units = convert_to_correct_units(dose_types[i], start_dates[i], end_dates[i], values[i])
        values[i] = basal_in_units

    assert len(dose_types) == len(start_dates) == len(end_dates) ==\
        len(values),\
        "expected output shape to match"

    return (dose_types, start_dates, end_dates, values)


def get_carb_data(dataframe_carbs, offset=0):
        """ Load carb information from an issue report cached_carbs dictionary

        Arguments:
        data -- dictionary containing cached carb information
        offset -- the offset from UTC in seconds

        Output:
        3 lists in (carb_values, carb_start_dates, carb_absorption_times)
        format
        """
        carb_values = [json.loads(dict_)['carbohydrate']['net'] for dict_ in dataframe_carbs['Nutrition']]
        
        start_dates = [
                datetime.strptime(
                        str(date).split('.')[0],
                        "%Y-%m-%d %H:%M:%S"
                ) + timedelta(seconds=offset)
                for date in dataframe_carbs['Local Time']
        ]
        absorption_times = [
        float(json.loads(dict_)['com.loopkit.AbsorptionTime']) / 60
        if json.loads(dict_)['com.loopkit.AbsorptionTime'] is not None
        else None for dict_ in dataframe_carbs['Payload']
    ]

        assert len(start_dates) == len(carb_values) == len(absorption_times),\
                "expected input shapes to match"
        return (start_dates, carb_values, absorption_times)


def seconds_to_time(seconds):
        """ Convert seconds since midnight into a datetime.time object """
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return time(int(hours), int(minutes), int(seconds))


def get_starts_and_ends_from_seconds(seconds_list):
        """ Given a list of seconds since midnight,
                convert into start and end times
        """
        starts = [seconds_to_time(seconds) for seconds in seconds_list]
        ends = [value for value in starts]
        ends.append(ends.pop(0))

        assert len(starts) == len(ends), "expected output shapes to match"

        return (starts, ends)


def get_sensitivities(data):
        """ Load insulin sensitivity schedule
                from an issue report isf_schedule dictionary

        Arguments:
        data -- dictionary containing ISF information

        Output:
        3 lists in (sensitivity_start_time, sensitivity_end_time,
                                sensitivity_value (mg/dL/U)) format
        """
        seconds = [float(dict_.get("startTime")) for dict_ in data]

        (start_times, end_times) = get_starts_and_ends_from_seconds(seconds)

        values = [dict_.get("value") for dict_ in data]

        assert len(start_times) == len(end_times) == len(values),\
                "expected output shape to match"

        return (start_times, end_times, values)


def get_carb_ratios(data):
        """ Load carb ratio schedule
                from an issue report carb_ratio_schedule dictionary

        Arguments:
        data -- dictionary containing CR information

        Output:
        2 lists in (ratio_start_time, ratio_value (g/U)) format
        """
        seconds = [float(dict_.get("startTime")) for dict_ in data]

        start_times = get_starts_and_ends_from_seconds(seconds)[0]

        values = [dict_.get("value") for dict_ in data]

        assert len(start_times) == len(values),\
                "expected output shape to match"

        return (start_times, values)


def get_basal_schedule(data):
        """ Load basal rate schedule
                from an issue report basal_rate_schedule dictionary

        Arguments:
        data -- dictionary containing basal schedule information

        Output:
        3 lists in (rate_start_time, rate_length (minutes), rate (U/hr)) format
        """
        seconds = [float(dict_.get("startTime")) for dict_ in data]
        rate_minutes = []
        for i in range(0, len(seconds)):
                if i == len(seconds) - 1:
                        rate_minutes.append(
                                (seconds[i] - seconds[0]) / 60
                        )
                else:
                        rate_minutes.append(
                                (seconds[i+1] - seconds[i]) / 60
                        )

        start_times = get_starts_and_ends_from_seconds(seconds)[0]

        values = [dict_.get("value") for dict_ in data]

        assert len(start_times) == len(rate_minutes) == len(values),\
                "expected output shapes to match"

        return (start_times, values, rate_minutes)


def get_target_range_schedule(data):
        """ Load target range schedule
                from an issue report "correction_range_schedule" dictionary
        """
        seconds = [float(dict_.get("startTime")) for dict_ in data]
        (start_times, end_times) = get_starts_and_ends_from_seconds(seconds)
        min_values = [float(dict_.get("value")[0]) for dict_ in data]
        max_values = [float(dict_.get("value")[1]) for dict_ in data]

        return (start_times, end_times, min_values, max_values)


def load_momentum_effects(data, offset=0):
        """ Load glucose momentum effects from a list """
        start_times = [
                datetime.strptime(
                        dict_.get("startDate"),
                        "%Y-%m-%d %H:%M:%S %z"
                ) + timedelta(seconds=offset)
                for dict_ in data
        ]
        values = [
                float(dict_.get("quantity")) for dict_ in data
        ]
        return (start_times, values)


def get_counteractions(data, offset=0):
        """ Load counteraction effect data from a list """
        start_times = [
                datetime.strptime(
                        dict_.get("start_time"),
                        "%Y-%m-%d %H:%M:%S %z"
                ) + timedelta(seconds=offset)
                for dict_ in data
        ]
        end_times = [
                datetime.strptime(
                        dict_.get("end_time"),
                        " %Y-%m-%d %H:%M:%S %z"
                ) + timedelta(seconds=offset)
                for dict_ in data
        ]
        values = [
                float(dict_.get("value")) for dict_ in data
        ]
        return (start_times, end_times, values)


def load_insulin_effects(data, offset=0):
        """ Load insulin effect data from a list """
        start_times = [
                datetime.strptime(
                        dict_.get("start_time"),
                        "%Y-%m-%d %H:%M:%S %z"
                ) + timedelta(seconds=offset)
                for dict_ in data
        ]
        values = [
                float(dict_.get("value")) for dict_ in data
        ]
        return (start_times, values)


def get_retrospective_effects(data, offset=0):
        """ Load retrospective effect data from a list """
        start_times = [
                datetime.strptime(
                        dict_.get("startDate"),
                        "%Y-%m-%d %H:%M:%S %z"
                ) + timedelta(seconds=offset)
                for dict_ in data
        ]
        values = [
                float(dict_.get("quantity")) for dict_ in data
        ]
        return (start_times, values)


def get_settings(data):
        """ Load needed settings from an issue report

        Arguments:
        data -- the parsed issue report dictionary

        Output:
        Dictionary of settings
        """
        settings = {}

        model = data.get("insulin_model")
        if not model:
                raise RuntimeError("No insulin model information found")

        if model.lower() == "humalognovologchild":
                settings["model"] = [
                        data.get("insulin_action_duration") / 60,
                        65
                ]
        elif model.lower() == "humalognovologadult":
                settings["model"] = [
                        data.get("insulin_action_duration") / 60,
                        75
                ]
        elif model.lower() == "fiasp":
                settings["model"] = [
                        data.get("insulin_action_duration") / 60,
                        55
                ]
        else:  # Walsh model
                settings["model"] = [
                        data.get("insulin_action_duration") / 60 / 60
                ]

        momentum_interval = data.get("glucose_store").get("momentumDataInterval")
        if momentum_interval is not None:
                settings["momentum_data_interval"] = float(momentum_interval) / 60
        else:
                settings["momentum_data_interval"] = 15

        suspend_threshold = data.get("suspend_threshold")
        if suspend_threshold is not None:
                settings["suspend_threshold"] = float(suspend_threshold)
        else:
                settings["suspend_threshold"] = None

        settings["dynamic_carb_absorption_enabled"] = True
        settings["retrospective_correction_integration_interval"] = 30
        settings["recency_interval"] = 15
        settings["retrospective_correction_grouping_interval"] = 30
        settings["rate_rounder"] = 0.05
        settings["insulin_delay"] = 10
        settings["carb_delay"] = 10

        settings["default_absorption_times"] = [
                float(data.get("carb_default_absorption_times_fast")) / 60,
                float(data.get("carb_default_absorption_times_medium")) / 60,
                float(data.get("carb_default_absorption_times_slow")) / 60
                ]

        settings["max_basal_rate"] = data.get("maximum_basal_rate")
        settings["max_bolus"] = data.get("maximum_bolus")
        settings["retrospective_correction_enabled"] = data.get(
                "retrospective_correction_enabled"
        ) and data.get(
                "retrospective_correction_enabled"
        ).lower() == "true"

        return settings


def get_last_temp_basal(data, offset=0):
        """ Load the last temporary basal from an issue report
                "last_temp_basal" dictionary
        """
        if (data.get(" type") == "LoopKit.DoseType.tempBasal"
                        or data.get("type") == "LoopKit.DoseType.tempBasal"):
                type_ = DoseType.tempbasal
        elif (data.get(" type") == "LoopKit.DoseType.basal"
                    or data.get("type") == "LoopKit.DoseType.basal"):
                type_ = DoseType.basal
        else:
                raise RuntimeError("The last temporary basal is not a basal")

        return [
                type_,
                datetime.strptime(
                        data.get(" startDate") if data.get(" startDate") is not None
                        else data.get("startDate"),
                        "%Y-%m-%d %H:%M:%S %z"
                ) + timedelta(seconds=offset),
                datetime.strptime(
                        data.get(" endDate") if data.get(" endDate") is not None
                        else data.get("endDate"),
                        "%Y-%m-%d %H:%M:%S %z"
                ) + timedelta(seconds=offset),
                float(data.get(" value")) if data.get(" value") is not None
                else float(data.get("value"))
        ]



# %% List management tools
def sort_by_first_list(list_1, list_2, list_3=None, list_4=None, list_5=None):
        """ Sort lists that are matched index-wise, using the first list as the
                property to sort by

        Example:
                l1: [50, 2, 3]               ->     [2, 3, 50]
                l2: [dog, cat, parrot]       ->     [cat, parrot, dog]
        """
        unsort_1 = numpy.array(list_1)
        unsort_2 = numpy.array(list_2)
        unsort_3 = numpy.array(list_3)
        unsort_4 = numpy.array(list_4)
        unsort_5 = numpy.array(list_5)

        sort_indexes = unsort_1.argsort()

        unsort_1.sort()
        list_1 = list(unsort_1)
        l2 = list(unsort_2[sort_indexes])
        if list_3:
                l3 = list(unsort_3[sort_indexes])
        else:
                l3 = []
        if list_4:
                l4 = list(unsort_4[sort_indexes])
        else:
                l4 = []
        if list_5:
                l5 = list(unsort_5[sort_indexes])
        else:
                l5 = []

        return (list_1, l2, l3, l4, l5)


def remove_too_new_values(
                sort_time,
                list_1, list_2, list_3=None, list_4=None, list_5=None,
                is_dose_data=False
                ):
        """ Remove values that occur after a certain date. This function makes the
                assumption that the date list is sorted in ascending order, and
                that all lists (if they are not None) are the same length. The first
                list must be the list with the times, unless is_dose_data is True,
                in which case the second list must contain the times.

        Arguments:
        sort_time -- the datetime after which to remove values
        """
        l1 = []
        l2 = []
        l3 = []
        l4 = []
        l5 = []

        for i in range(0, len(list_1)):
                # if this isn't dose data, use the first list to sort
                if not is_dose_data and list_1[i] <= sort_time:
                        l1.append(list_1[i])
                        l2.append(list_2[i])
                        if list_3:
                                l3.append(list_3[i])
                        if list_4:
                                l4.append(list_4[i])
                        if list_5:
                                l5.append(list_5[i])
                # otherwise, use the second list to sort
                elif is_dose_data and list_2[i] <= sort_time:
                        l1.append(list_1[i])
                        l2.append(list_2[i])
                        if list_3:
                                l3.append(list_3[i])
                        if list_4:
                                l4.append(list_4[i])
                        if list_5:
                                l5.append(list_5[i])

        return (l1, l2, l3, l4, l5)


# %% Take an issue report and run it through the Loop algorithm
def parse_report_and_run(path, name):
        return parse_report_and_run_with_name(os.path.join(path, name))


# TO DO!
# TO DO: ADD ANOTHER METHOD THAT IS SIMILAR, 
# BUT THAT ALSO TAKES IN A DATE FROM WHICH TO CALCULATE PREDICTIONS,
# AND THAT RETURNS A LIST OF MEASURED VALUES TO COMPARE PREDICTIONS WITH!

 # %% Take an issue report and run it through the Loop algorithm
def parse_report_and_run_with_name(data_path_and_name):
    """ Get relevent information from a Loop issue report and use it to
            run PyLoopKit

    Arguments:
    path -- the path to the issue report
    name -- the name of the file, with the .json extension

    Output:
    A dictionary of all 4 effects, the predicted glucose values, and the
    recommended basal and bolus
    """

    settings_name = "therapy_settings.json"
    settings_path = "pyloopkit/example_files/"
    settings_path_and_name = os.path.join(settings_path, settings_name)
    with open(settings_path_and_name, "r") as file:
        settings_dict = json.load(file)

    # Load data
    dataframe_glucose = pd.read_excel(data_path_and_name, 'CGM')
    dataframe_bolus = pd.read_excel(data_path_and_name, 'Bolus')
    dataframe_basal = pd.read_excel(data_path_and_name, 'Basal')
    dataframe_carbs = pd.read_excel(data_path_and_name, 'Food')

    input_dict = {}

    # Set offset=0 because the Tidepool export has a column for local time
    # Note that this is not a good practice in case of changing time zones
    # This should be handled in a better way
    offset = 0
    
    if not dataframe_glucose.empty:
            (glucose_dates, glucose_values) = get_glucose_data(
                    dataframe_glucose, 
                    offset
            )
            # Time to run is the date at which the prediction will be calculated
            # We use the first glucose measurement in the list (sorted descending)
            time_to_run = glucose_dates[0]
            (glucose_dates, glucose_values) = remove_too_new_values(
                    time_to_run,
                    *sort_by_first_list(
                            glucose_dates, glucose_values
                    )[0:2]
            )[0:2]
            input_dict["glucose_dates"] = glucose_dates
            input_dict["glucose_values"] = glucose_values
            input_dict["glucose_units"] = "mg/dL"

    else:
            raise RuntimeError("No glucose information found")

    input_dict["time_to_calculate_at"] = time_to_run

    if not (dataframe_bolus.empty or  dataframe_basal.empty):
            (dose_types,
             dose_starts,
             dose_ends,
             dose_values
             ) = get_insulin_data(
                    dataframe_bolus, 
                    dataframe_basal,
                    offset,
                    #entry_to_add=issue_dict.get("get_normalized_dose_entries")[-1],
                    now_time=time_to_run
            )
    else:
            warnings.warn("Warning: no insulin dose information found")
            (dose_types,
             dose_starts,
             dose_ends,
             dose_values
             ) = ([], [], [], [])


    (dose_types,
     dose_starts,
     dose_ends,
     dose_values
     ) = remove_too_new_values(
             time_to_run,
             *sort_dose_lists(
                     dose_types,
                     dose_starts,
                     dose_ends,
                     dose_values
             )[0:4],
             is_dose_data=True
    )[0:4]
    input_dict["dose_types"] = dose_types
    input_dict["dose_start_times"] = dose_starts
    input_dict["dose_end_times"] = dose_ends
    input_dict["dose_values"] = dose_values
    input_dict["dose_value_units"] = "U or U/hr"
    input_dict["dose_delivered_units"] = [None for i in range(len(dose_types))]

    if not dataframe_carbs.empty:
            (carb_dates,
             carb_values,
             carb_absorptions
             ) = sort_by_first_list(
                             *get_carb_data(
                                     dataframe_carbs,
                                     offset,
                             )
            )[0:3]
    else:
            (carb_dates,
             carb_values,
             carb_absorptions
             ) = ([], [], [])

    input_dict["carb_dates"] = carb_dates
    input_dict["carb_values"] = carb_values
    input_dict["carb_absorption_times"] = carb_absorptions
    input_dict["carb_value_units"] = "g"

    settings = get_settings(settings_dict)
    input_dict["settings_dictionary"] = settings

    if settings_dict.get(
                    "insulin_sensitivity_factor_schedule"):
            (sensitivity_start_times,
             sensitivity_end_times,
             sensitivity_values
             ) = get_sensitivities(
                    settings_dict.get(
                            "insulin_sensitivity_factor_schedule"
                    )
            )
    else:
            raise RuntimeError("No insulin sensitivity information found")
    (sensitivity_start_times,
     sensitivity_end_times,
     sensitivity_values
     ) = sort_by_first_list(
             sensitivity_start_times,
             sensitivity_end_times,
             sensitivity_values
    )[0:3]

    input_dict["sensitivity_ratio_start_times"] = sensitivity_start_times
    input_dict["sensitivity_ratio_end_times"] = sensitivity_end_times
    input_dict["sensitivity_ratio_values"] = sensitivity_values
    input_dict["sensitivity_ratio_value_units"] = "mg/dL/U"

    if settings_dict.get("carb_ratio_schedule"):
            (carb_ratio_starts,
             carb_ratio_values
             ) = get_carb_ratios(
                    settings_dict.get("carb_ratio_schedule")
            )
    else:
            raise RuntimeError("No carb ratio information found")
    (carb_ratio_starts,
     carb_ratio_values
     ) = sort_by_first_list(
             carb_ratio_starts,
             carb_ratio_values
     )[0:2]

    input_dict["carb_ratio_start_times"] = carb_ratio_starts
    input_dict["carb_ratio_values"] = carb_ratio_values
    input_dict["carb_ratio_value_units"] = "g/U"

    if settings_dict.get("basal_rate_schedule"):
            (basal_rate_starts,
             basal_rate_values,
             basal_rate_minutes
             ) = get_basal_schedule(
                    settings_dict.get("basal_rate_schedule")
            )
    else:
            raise RuntimeError("No basal rate information found")
    (basal_rate_starts,
     basal_rate_minutes,
     basal_rate_values
     ) = sort_by_first_list(
             basal_rate_starts,
             basal_rate_minutes,
             basal_rate_values
     )[0:3]

    input_dict["basal_rate_start_times"] = basal_rate_starts
    input_dict["basal_rate_minutes"] = basal_rate_minutes
    input_dict["basal_rate_values"] = basal_rate_values
    input_dict["basal_rate_units"] = "U/hr"

    if settings_dict.get("correction_range_schedule"):
            (target_range_starts,
             target_range_ends,
             target_range_minimum_values,
             target_range_maximum_values
             ) = get_target_range_schedule(
                    settings_dict.get("correction_range_schedule")
            )
            (target_range_starts,
             target_range_ends,
             target_range_minimum_values,
             target_range_maximum_values
             ) = sort_by_first_list(
                     target_range_starts,
                     target_range_ends,
                     target_range_minimum_values,
                     target_range_maximum_values
             )[0:4]
    else:
            raise RuntimeError("No target range rate information found")

    input_dict["target_range_start_times"] = target_range_starts
    input_dict["target_range_end_times"] = target_range_ends
    input_dict["target_range_minimum_values"] = target_range_minimum_values
    input_dict["target_range_maximum_values"] = target_range_maximum_values
    input_dict["target_range_value_units"] = "mg/dL"

    # TO DO: Add last temp basal
    last_temp_basal = []

    input_dict["last_temporary_basal"] = last_temp_basal

    recommendations = update(
            input_dict
            )

    return recommendations


def parse_dictionary_from_previous_run(path, name):
        """ Get a dictionary output from a previous run of PyLoopKit
                and convert the ISO strings to datetime or time objects, and
                dose types to enums
        """
        data_path_and_name = os.path.join(path, name)

        with open(data_path_and_name, "r") as file:
                dictionary = json.load(file)

        keys_with_times = [
                "basal_rate_start_times",
                "carb_ratio_start_times",
                "sensitivity_ratio_start_times",
                "sensitivity_ratio_end_times",
                "target_range_start_times",
                "target_range_end_times"
                ]

        for key in keys_with_times:
                new_list = []
                for string in dictionary.get(key):
                        new_list.append(time.fromisoformat(string))
                dictionary[key] = new_list

        keys_with_datetimes = [
                "dose_start_times",
                "dose_end_times",
                "glucose_dates",
                "carb_dates"
                ]

        for key in keys_with_datetimes:
                new_list = []
                for string in dictionary.get(key):
                        new_list.append(datetime.fromisoformat(string))
                dictionary[key] = new_list

        dictionary["time_to_calculate_at"] = datetime.fromisoformat(
                dictionary["time_to_calculate_at"]
        )

        last_temp = dictionary.get("last_temporary_basal")
        dictionary["last_temporary_basal"] = [
                DoseType.from_str(last_temp[0]),
                datetime.fromisoformat(last_temp[1]),
                datetime.fromisoformat(last_temp[2]),
                last_temp[3]
        ]

        dictionary["dose_types"] = [
                DoseType.from_str(value) for value in dictionary.get("dose_types")
        ]

        output = update(dictionary)

        return output




