


'''
extension GlucoseEffectVelocity {
    static let perSecondUnit = HKUnit.milligramsPerDeciliter.unitDivided(by: .second())

    /// The integration of the velocity span
    public var effect: GlucoseEffect {
        let duration = endDate.timeIntervalSince(startDate)
        let velocityPerSecond = quantity.doubleValue(for: GlucoseEffectVelocity.perSecondUnit)

        return GlucoseEffect(
            startDate: endDate,
            quantity: HKQuantity(
                unit: .milligramsPerDeciliter,
                doubleValue: velocityPerSecond * duration
            )
        )
    }
}
'''

class GlucoseEffectVelocity:
    def __init__ (self, startDate, endDate, quantity, unit):
        self.startDate = startDate
        self.endDate = endDate
        self.quantity = quantity
        self.unit = unit






