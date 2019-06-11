
from LoopKitTests import loadFixture, dateFormatter, HKQuantity
from GlucoseEffect import GlucoseEffect
from GlucoseEffectVelocity import GlucoseEffectVelocity
import json

class GlucoseFixtureValue:
    def __init__ (self, startDate, quantity, isDisplayOnly, provenanceIdentifier, unit):
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

    # have to specify folder if the file is within one
    def loadInputFixture (resourceName):
        fixture = loadFixture (resourceName)

        def glucoseFixtureMaker (dict):
            return GlucoseFixtureValue (dateFormatter (dict.get("date")), 
                                        HKQuantity (dict.get("unit"), dict.get("amount")), 
                                        dict.get("display_only") or False, 
                                        dict.get("provenance_identifier"), 
        return map(glucoseFixtureMaker, fixture)


    def loadOutputFixture (resourceName):
        fixture = loadFixture (resourceName)

        def glucoseEffectMaker (dict):
            return GlucoseEffect(dateFormatter (dict.get("date")), 
                                 HKQuantity (dict.get("unit"), dict.get("amount"))  )

        return map (glucoseEffectMaker, fixture)



    def loadEffectVelocityFixture (resourceName):
        fixture = loadFixture(resourceName)

        def glucoseEffectVelocityMaker (dict):
            return GlucoseEffectVelocity(dateFormatter (dict.get("startDate")), 
                                         dateFormatter (dict.get("endDate")), 
                                         HKQuantity (dict.get("unit"), dict.get("value") ) )
                                         





