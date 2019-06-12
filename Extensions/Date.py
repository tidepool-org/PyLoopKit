
from LoopKitTests import dateFormatter
import math, datetime

# timeIntervalSinceReferenceDate is the number of seconds since January, 1st, 2001: 12:00 am (mid night)
def timeIntervalSinceReferenceDate (obj):
    refTime = dateFormatter ("2001-01-01T00:00:00")
    actualTime = obj.startDate
    dif = abs (actualTime - refTime)

    return dif

def dateFlooredToTimeInterval (obj, interval):
    if interval == 0:
        return obj
    refTime = dateFormatter ("2001-01-01T00:00:00")             # this assumes the interval is in mins
    flooredDelta = math.floor (timeIntervalSinceReferenceDate(obj) / interval / 60) * interval * 60

    return refTime + datetime.timedelta(seconds=flooredDelta)

def dateCeiledToTimeInterval (obj, interval):
    if interval == 0:
        return obj
    refTime = dateFormatter ("2001-01-01T00:00:00")             # this assumes the interval is in mins
    ceiledDelta = math.ceil (timeIntervalSinceReferenceDate(obj) / interval / 60) * interval * 60

    return refTime + datetime.timedelta(seconds=ceiledDelta)


