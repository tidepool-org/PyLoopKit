
from LoopKitTests import loadFixture
import json

'''
public struct GlucoseFixtureValue: GlucoseSampleValue {
    public let startDate: Date
    public let quantity: HKQuantity
    public let isDisplayOnly: Bool
    public let provenanceIdentifier: String

    public init(startDate: Date, quantity: HKQuantity, isDisplayOnly: Bool, provenanceIdentifier: String?) {
        self.startDate = startDate
        self.quantity = quantity
        self.isDisplayOnly = isDisplayOnly
        self.provenanceIdentifier = provenanceIdentifier ?? "com.loopkit.LoopKitTests"
    }
}


extension GlucoseFixtureValue: Comparable {
    public static func <(lhs: GlucoseFixtureValue, rhs: GlucoseFixtureValue) -> Bool {
        return lhs.startDate < rhs.startDate
    }

    public static func ==(lhs: GlucoseFixtureValue, rhs: GlucoseFixtureValue) -> Bool {
        return lhs.startDate == rhs.startDate &&
               lhs.quantity == rhs.quantity &&
               lhs.isDisplayOnly == rhs.isDisplayOnly &&
               lhs.provenanceIdentifier == rhs.provenanceIdentifier
    }
}
'''

class GlucoseFixtureValue:
    def __init__ (self, startDate, quantity, isDisplayOnly, provenanceIdentifier):
        self.startDate = startDate
        self.quantity = quantity
        self.isDisplayOnly = isDisplayOnly
        self.provenanceIdentifier = provenanceIdentifier or "com.loopkit.LoopKitTests"

    def __lt__ (self, other):
        return self.startDate < other.startDate

    def __eq__ (self, other):
        return (self.startDate == other.startDate and
                self.quantity == other.quantity and
                self.isDisplayOnly == other.isDisplayOnly and
                self.provenanceIdentifier == other.provenanceIdentifier)



def runTestCases ():
    '''
    func loadInputFixture(_ resourceName: String) -> [GlucoseFixtureValue] {
        let fixture: [JSONDictionary] = loadFixture(resourceName)
        let dateFormatter = ISO8601DateFormatter.localTimeDate()

        return fixture.map {
            return GlucoseFixtureValue(
                startDate: dateFormatter.date(from: $0["date"] as! String)!,
                quantity: HKQuantity(unit: HKUnit.milligramsPerDeciliter, doubleValue: $0["amount"] as! Double),
                isDisplayOnly: ($0["display_only"] as? Bool) ?? false,
                provenanceIdentifier: $0["provenance_identifier"] as? String
            )
        }
    }
    '''

    # have to specify folder if the file is within one
    def loadInputFixture (resourceName):
        fixture = loadFixture (resourceName)

        def glucoseObjectMaker (dict):
            return GlucoseFixtureValue (dict.get("startDate"), dict.get("quantity"), 
                                    dict.get("isDisplayOnly") or False, dict.get("provenanceIdentifier"))

        return map(glucoseObjectMaker, fixture)


    '''
	func loadOutputFixture(_ resourceName: String) -> [GlucoseEffect] {
        let fixture: [JSONDictionary] = loadFixture(resourceName)
        let dateFormatter = ISO8601DateFormatter.localTimeDate()

        return fixture.map {
            return GlucoseEffect(startDate: dateFormatter.date(from: $0["date"] as! String)!, quantity: HKQuantity(unit: HKUnit(from: $0["unit"] as! String), doubleValue: $0["amount"] as! Double))
        }
    }

    '''

    # returns GlucoseEffect object
    def loadOutputFixture (resourceName):
    	fixture = loadFixture (resourceName)
!    	# find equiv for ISO8601DateFormatter.localTimeDate()
    	dateFormatter = ISO8601DateFormatter.localTimeDate()
!		# need to work on loading fixture b4 I can get to looping over the data bc I need to know the type


