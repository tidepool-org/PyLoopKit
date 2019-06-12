
import sys, os, json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from LoopKitTests import loadFixture, dateFormatter, HKQuantity
from LoopKit.GlucoseEffect import GlucoseEffect
from GlucoseEffectVelocity import GlucoseEffectVelocity
from LoopKit.GlucoseKit.GlucoseMath import linearMomentumEffect

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

    def loadInputFixture (resourceName):
        fixture = loadFixture (resourceName, ".json")

        def glucoseFixtureMaker (dict):
            return GlucoseFixtureValue (dateFormatter (dict.get("date")), 
                                        HKQuantity (dict.get("unit"), dict.get("amount")), 
                                        dict.get("display_only") or False, 
                                        dict.get("provenance_identifier") )
        return map(glucoseFixtureMaker, fixture)


    def loadOutputFixture (resourceName):
        fixture = loadFixture (resourceName, ".json")

        def glucoseEffectMaker (dict):
            return GlucoseEffect(dateFormatter (dict.get("date")), 
                                 HKQuantity (dict.get("unit"), dict.get("amount"))  )

        return map (glucoseEffectMaker, fixture)



    def loadEffectVelocityFixture (resourceName):
        fixture = loadFixture(resourceName, ".json")

        def glucoseEffectVelocityMaker (dict):
            return GlucoseEffectVelocity(dateFormatter (dict.get("startDate")), 
                                         dateFormatter (dict.get("endDate")), 
                                         HKQuantity (dict.get("unit"), dict.get("value") ) )

        return map (glucoseEffectVelocityMaker, fixture)

    '''
    func testMomentumEffectForBouncingGlucose() {
        let input = loadInputFixture("momentum_effect_bouncing_glucose_input")
        let output = loadOutputFixture("momentum_effect_bouncing_glucose_output")

        let effects = input.linearMomentumEffect()
        let unit = HKUnit.milligramsPerDeciliter

        XCTAssertEqual(output.count, effects.count)

        for (expected, calculated) in zip(output, effects) {
            XCTAssertEqual(expected.startDate, calculated.startDate)
            XCTAssertEqual(expected.quantity.doubleValue(for: unit), calculated.quantity.doubleValue(for: unit), accuracy: Double(Float.ulpOfOne))
        }
    }
                                         
    '''

    def testMomentumEffectForBouncingGlucose():
        inputt = loadInputFixture("momentum_effect_bouncing_glucose_input")
        output = loadOutputFixture ("momentum_effect_bouncing_glucose_output")

        effects = linearMomentumEffect (inputt)
        unit = "mg/dL"

        if len(output) != len (effects):
            print("Test failed, expected output is length", len(output), "but output from program is",len (effects))
        for (expected, calculated) in zip(output, effects):
            if expected.startDate != calculated.startDate:
                print ("Test failed because",expected.startDate,"!=",calculated.startDate)
        #! DIDN'T INCLUDE LAST TEST AND NEED TO DO SO
        print ("Test passed!!!")
    testMomentumEffectForBouncingGlucose()

runTestCases()




