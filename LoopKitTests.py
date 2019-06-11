
import json, os
from datetime import datetime

def loadFixture (resourceName):
	script_dir = os.path.dirname(__file__)
	return json.load( open(str(script_dir) + str(resourceName) + ".json"))


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

# converts string to d
def dateFormatter (dateString):
	isoDate = datetime.strptime (dateString, "%Y-%m-%dT%H:%M:%S").isoformat()

	return isoDate