from pyloopkit.tidepool_api.tidepool_api import TidepoolAPI
from datetime import datetime, timedelta
import json

from pyloopkit.tidepool_api_parser import (
    get_glucose_data
)



tp_api = TidepoolAPI('miriamkwolff@outlook.com', 'l4mz1b7aYztG')
tp_api.login()

# Default use the data from the last 24 hours
start_date = datetime.now() - timedelta(days=1)
end_date = datetime.now()

# Uncomment the lines below to customize days
#start_date = dt.datetime(2023, 1, 1)
#end_date = dt.datetime(2023, 1, 2) # year, month, day

# All the data in json format
user_data = tp_api.get_user_event_data(start_date, end_date)

tp_api.logout()

#print(user_data)

#data = json.loads(user_data[0])

glucose_data = []
bolus_data = []
basal_data = []
carb_data = []

# Sort data types into lists
for data in user_data:
	if data['type'] == 'cbg':
		glucose_data.append(data)
	elif data['type'] == 'bolus':
		bolus_data.append(data)
	elif data['type'] == 'basal':
		basal_data.append(data)
	elif data['type'] == 'food':
		carb_data.append(data)


#print(data)
#print(data['type'])

#print(glucose_data)

now = datetime.now()
utcNow = datetime.utcnow()
offset = int((now - utcNow).total_seconds())
print(get_glucose_data(glucose_data, offset=offset))

#offset = now.total_seconds()


#print(offset)

#time_zone_name = glucose_data[0]['payload']['HKTimeZone']
#time_zone = pytz.timezone(time_zone_name)
#now = datetime.now(time_zone)
#offset = now.utcoffset().total_seconds()


#print(get_glucose_data(glucose_data, offset=offset))

#print(offset)






# TO DO:
# Get the parser to work with this
# Create a command line interface for writing in credentials








