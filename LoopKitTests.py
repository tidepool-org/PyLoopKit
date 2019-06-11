
import json, os

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
