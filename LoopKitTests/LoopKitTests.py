
import json, os
from datetime import datetime

class HKQuantity:
    def __init__ (self, unit, doubleValue):
        self.unit = unit
        self.doubleValue = doubleValue

    def __lt__ (self, other):
        selfValue = self.doubleValue
        otherValue = other.doubleValue
        if self.unit == "mmol":
            selfValue *= 18
        if other.unit == "mmol":
            otherValue *= 18
        return selfValue < otherValue

    def __gt__ (self, other):
        selfValue = self.doubleValue
        otherValue = other.doubleValue
        if self.unit == "mmol":
            selfValue *= 18
        if other.unit == "mmol":
            otherValue *= 18
        return selfValue > otherValue

    def __eq__ (self, other):
        selfValue = self.doubleValue
        otherValue = other.doubleValue
        if self.unit == "mmol":
            selfValue *= 18
        if other.unit == "mmol":
            otherValue *= 18
        return selfValue == otherValue


def loadFixture (resourceName, extension):
    searchDir = os.path.dirname(__file__)
    for root, dirs, files in os.walk(searchDir):
        for name in files:
            pathEnd = os.path.basename(name)
            (base, ext) = os.path.splitext(name)
            if base == resourceName and extension == ext:
                return os.path.join(root, name)
    print ("No file found for that key")
    return ""

'''
extension ISO8601DateFormatter {
    static func localTimeDateFormatter() -> Self {
        let formatter = self.init()

        formatter.formatOptions = .withInternetDateTime
        formatter.formatOptions.subtract(.withTimeZone)
        formatter.timeZone = .current

        return formatter
    }
'''


'''
extension DateFormatter {
    static var descriptionFormatter: DateFormatter {
        let formatter = self.init()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ssZZZZZ"

        return formatter
    }
}
'''

# converts string to datetime object in the ISO 8601 format
def dateFormatter (dateString):
    try:
        isoDate = datetime.strptime (dateString, "%Y-%m-%dT%H:%M:%S").isoformat()

    # this still errors, figure out why (it's an edge-case for some of the testcases)
    except:
        isoDate = datetime.strptime (dateString, "%Y-%m-%dT%H:%M:%S%z").isoformat()
    return isoDate
