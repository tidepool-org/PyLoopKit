# -*- coding: utf-8 -*-
"""get_donor_data_and_metadata.py
In the context of the big data donation
project, this code grabs donor data and metadata.

This code calls accept_new_donors_and_get_donor_list.py
to get the most recent donor list
"""

# %% REQUIRED LIBRARIES
import pandas as pd
import datetime as dt
import numpy as np
import os
import sys
import getpass
import requests
import json
import pdb
import argparse

from datetime import datetime, timedelta
import datetime as dt
envPath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if envPath not in sys.path:
    sys.path.insert(0, envPath)


# %% USER INPUTS (choices to be made in order to run the code)
codeDescription = "execute pyLoopKit"
parser = argparse.ArgumentParser(description=codeDescription)

parser.add_argument(
    "-d",
    "--date-stamp",
    dest="time_to_calculate_at",
    default=dt.datetime.now().strftime('%b %d %Y %I:%M%p'),
    help="date, in '%b %d %Y %I:%M%p' format, the day from when to calculate the pyLoopKit "

)


parser.add_argument(
    "-dg",
    "--donor-group",
    dest="donor_group",
    default=np.nan,
    help="name of the donor group in the tidepool .env file"
)

parser.add_argument(
    "-u",
    "--userid",
    dest="userid_of_shared_user",
    default=np.nan,
    help="userid of account shared with the donor group or master account"
)


parser.add_argument(
    "-e",
    "--email",
    dest="email",
    default=np.nan,
    help="email address of the master account"
)

parser.add_argument(
    "-p",
    "--password",
    dest="password",
    default=np.nan,
    help="password of the master account"
)

parser.add_argument(
    "-o",
    "--output-data-path",
    dest="data_path",
    default=os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "data"
        )
    ),
    help="the output path where the data is stored"
)



args = parser.parse_args()


# %% FUNCTIONS
def make_folder_if_doesnt_exist(folder_paths):
    ''' function requires a single path or a list of paths'''
    if not isinstance(folder_paths, list):
        folder_paths = [folder_paths]
    for folder_path in folder_paths:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    return


def get_data_api(userid, startDate, endDate, headers):

    startDate = startDate.strftime("%Y-%m-%d") + "T00:00:00.000Z"
    endDate = endDate.strftime("%Y-%m-%d") + "T23:59:59.999Z"

    api_call = (
        "https://api.tidepool.org/data/" + userid + "?" +
        "endDate=" + endDate + "&" +
        "startDate=" + startDate + "&" +
        "dexcom=true" + "&" +
        "medtronic=true" + "&" +
        "carelink=true"
    )

    api_response = requests.get(api_call, headers=headers)
    if(api_response.ok):
        json_data = json.loads(api_response.content.decode())
        df = pd.DataFrame(json_data)
        print("getting data between %s and %s" % (startDate, endDate))

    else:
        sys.exit(
            "ERROR in getting data between %s and %s" % (startDate, endDate),
            api_response.status_code
        )

    endDate = pd.to_datetime(startDate) - pd.Timedelta(1, unit="d")

    return df, endDate


def get_data(
    time_to_calculate_at,
    donor_group=np.nan,
    userid_of_shared_user=np.nan,
    email=np.nan,
    password=np.nan
):
    # login
    if pd.notnull(donor_group):
        if donor_group == "bigdata":
            dg = ""
        else:
            dg = donor_group


    time_to_calculate_at = input("Enter the data time to execute from (format like Sep 01 2019  11:59PM) : ")

    if pd.isnull(email):
        email = input("Enter Tidepool email address:\n")

    if pd.isnull(password):
        password = getpass.getpass("Enter password:\n")

    auth = (email, password)

    api_call = "https://api.tidepool.org/auth/login"
    api_response = requests.post(api_call, auth=auth)
    if(api_response.ok):
        xtoken = api_response.headers["x-tidepool-session-token"]
        userid_master = json.loads(api_response.content.decode())["userid"]
        headers = {
            "x-tidepool-session-token": xtoken,
            "Content-Type": "application/json"
        }
    else:
        sys.exit("Error with " + auth[0] + ":" + str(api_response.status_code))

    if pd.isnull(userid_of_shared_user):
        userid_of_shared_user = input("Enter Tidepool userid (defaults to the email accounts userid):\n")
        if pd.isnull(userid_of_shared_user) or userid_of_shared_user == '':
            userid_of_shared_user = userid_master
        print(
            "getting data for the master account since no shared " +
            "user account was given"
        )

    print("logging into", auth[0], "...")

    # download user data
    print("downloading data ...")
    df = pd.DataFrame()
    endDate  = dt.datetime.strptime(time_to_calculate_at, '%b %d %Y %I:%M%p')
    startDate = endDate - timedelta(20)

    df, _ = get_data_api(
        userid_of_shared_user,
        startDate,
        endDate,
        headers
        )

    # logout
    api_call = "https://api.tidepool.org/auth/logout"
    api_response = requests.post(api_call, auth=auth)

    if(api_response.ok):
        print("successfully logged out of", auth[0])

    else:
        sys.exit(
            "Error with logging out for " +
            auth[0] + ":" + str(api_response.status_code)
        )
    df.to_csv("temp.csv")
    return df, userid_of_shared_user


# %% START OF CODE
def get_dataset(
    time_to_calculate_at,
    donor_group=np.nan,
    userid_of_shared_user=np.nan,
    auth=np.nan,
    email=np.nan,
    password=np.nan
):

    # get dataset

    data, userid = get_data(
        time_to_calculate_at=time_to_calculate_at,
        donor_group=donor_group,
        userid_of_shared_user=userid_of_shared_user,
        email=email,
        password=password
    )


    loop_input_dict = {}

    settings_dictionary = {}
    settings_dictionary["model"] = [360.0, 75]
    settings_dictionary["momentum_data_interval"] = 15
    settings_dictionary["suspend_threshold"] = 70
    settings_dictionary["dynamic_carb_absorption_enabled"] = True
    settings_dictionary["retrospective_correction_integration_interval"] = 30
    settings_dictionary["recency_interval"] = 15
    settings_dictionary["retrospective_correction_grouping_interval"] = 30
    settings_dictionary["rate_rounder"] = 0.05
    settings_dictionary["insulin_delay"] = 10
    settings_dictionary["carb_delay"] = 10
    settings_dictionary["default_absorption_times"] = [120.0, 180.0, 240.0]
    settings_dictionary["retrospective_correction_enabled"] = True
    loop_input_dict['settings_dictionary'] = settings_dictionary

    loop_input_dict['offset_applied_to_dates'] = 0

    #question - are these correct??
    loop_input_dict['target_range_start_times'] = ['12/31/1899 12:00:00 AM']
    loop_input_dict['target_range_end_times'] = ['12/31/1899 12:00:00 AM']
    loop_input_dict['target_range_minimum_values'] = ['90']
    loop_input_dict['target_range_maximum_values'] = ['100']
    loop_input_dict['target_range_value_units'] = ['mg/dL']


    #basal rate
    basal_df = data[data.type == 'basal']
    loop_input_dict['basal_rate_start_times'] = basal_df['time'].tolist()
    loop_input_dict['basal_rate_values'] = basal_df['rate'].tolist()
    basal_df['duration_by_min'] = basal_df['duration'].apply(lambda x: (x / (1000 * 60)) % 60)
    loop_input_dict['basal_rate_minutes'] = basal_df['duration_by_min'].tolist()
    loop_input_dict['basal_rate_units'] = 'U/hr'

    #dose - basal
    num_of_rows = basal_df.shape[0]
    dose_start_times = []
    dose_end_times = []
    dose_values = []
    dose_type = []
    dose_value_units = []
    max_basal_value = -100
    for index, row in basal_df.head(num_of_rows).iterrows():
        #building for the basal rate
        ##basal_rate_units.append('U/hr')
        basal_rate = row['rate']
        if basal_rate > max_basal_value:
            max_basal_value = basal_rate

        suppressed = row['suppressed']
        if not pd.isnull(suppressed):
            duration = row['duration']
            start_time = pd.to_datetime(row['time'])
            dose_start_times.append(start_time)
            dose_end_times.append(start_time + dt.timedelta(milliseconds=duration))
            suppressed_basal_rate = suppressed['rate']
            dose_values.append(suppressed_basal_rate)
            if suppressed_basal_rate > max_basal_value:
                max_basal_value = suppressed_basal_rate

            dose_type.append("DoseType.basal")
            dose_value_units.append("U/hr")

    settings_dictionary['max_basal_rate'] = max_basal_value

    loop_input_dict['dose_start_times'] = dose_start_times
    loop_input_dict['dose_end_times'] = dose_end_times
    loop_input_dict['dose_values'] = dose_values
    loop_input_dict['dose_type'] = dose_type
    loop_input_dict['dose_value_units'] = dose_value_units


    # dose - bolus
    bolus_df = data[data.type == 'bolus']
    num_of_rows = bolus_df.shape[0]
    max_bolus_value = -100
    for index, row in bolus_df.head(num_of_rows).iterrows():
        duration = row['duration']
        start_time = pd.to_datetime(row['time'])
        dose_start_times.append(start_time)
        dose_end_times.append(start_time) ##start_time + dt.timedelta(milliseconds=duration))
        bolus_value = row['normal']
        if bolus_value > max_bolus_value:
            max_bolus_value = bolus_value
        dose_values.append(bolus_value)
        dose_type.append("DoseType.bolus")
        dose_value_units.append("U")

    loop_input_dict['dose_start_times'] = dose_start_times
    loop_input_dict['dose_end_times'] = dose_end_times
    loop_input_dict['bolus_value'] = bolus_value
    loop_input_dict['dose_type'] = dose_type
    loop_input_dict['dose_value_units'] = 'U or U/hr' ##should this be a list??

    settings_dictionary['max_bolus'] = max_bolus_value

    carb_values = []
    carb_dates = []
    carb_value_units = []
    carb_absorption_times = []
    food_df = data[data.type == 'food']
    num_of_rows = food_df.shape[0]

    bolus_df['time'] = pd.to_datetime(bolus_df['time'])

    carb_ratio_start_times = []
    carb_ratio_values = []
    carb_ratio_value_units = []

    for index, row in food_df.head(num_of_rows).iterrows():
        carbohydrate = row['nutrition']["carbohydrate"]
        carb_value = carbohydrate['net']
        carb_values.append(carb_value)
        carb_dates.append(row['time'])
        carb_absorption_times.append(120)
        carb_value_units.append(carbohydrate['units'])

        ##calculate carb_ratio
        carb_time = pd.to_datetime(row['time'])
        from_date = carb_time - dt.timedelta(minutes=5)
        to_date = carb_time + dt.timedelta(minutes=5)
        mask = (bolus_df['time'] >= from_date) & (bolus_df['time'] <= to_date)
        single_bolus_df = bolus_df.loc[mask]

        #only capture events that are 1 food event to 1 bolus event
        if single_bolus_df.shape[0] == 1:
            #todo: sum values if we fine more than 1 within the 10 mins?
            #question - if we get more than one carb value within x time should we combine?
            bolus_val = single_bolus_df['normal'].iloc[0]
            carb_bolus_ratio = carb_value/bolus_val
            carb_ratio_start_times.append(carb_time)
            carb_ratio_values.append(carb_bolus_ratio)
            carb_ratio_value_units.append('g/U')

    loop_input_dict['carb_value'] = carb_value
    loop_input_dict['carb_dates'] = carb_dates
    loop_input_dict['carb_absorption_times'] = carb_absorption_times
    loop_input_dict['carb_value_units'] = carb_value_units
    loop_input_dict['carb_ratio_start_times'] = carb_ratio_start_times
    loop_input_dict['carb_ratio_values'] = carb_ratio_values
    loop_input_dict['carb_ratio_value_units'] = carb_ratio_value_units

    cbg_df = data[data.type == 'cbg']
    glucose_dates = []
    glucose_values = []
    glucose_units = []
    num_of_rows = cbg_df.shape[0]
    for index, row in cbg_df.head(num_of_rows).iterrows():
        glucose_dates.append(row['time'])
        glucose_values.append(row['value'])
        glucose_units.append([row['units']])

    loop_input_dict['glucose_dates'] = glucose_dates
    loop_input_dict['glucose_values'] = glucose_values
    loop_input_dict['glucose_units'] = glucose_units

    return data



if __name__ == "__main__":
    #time_to_calculate_at = 'Sep 01 2019  11:59PM'
    get_dataset(
        time_to_calculate_at=args.time_to_calculate_at,
        donor_group=args.donor_group,
        userid_of_shared_user=args.userid_of_shared_user,
        email=args.email,
        password=args.password
    )
