

class GlucoseEffect:
	def __init__ (self, startDate, quantity, unit):
		self.startDate = startDate
        self.quantity = quantity
        self.unit = unit

    def __ls__ (self, other):
    	return self.startDate < other.startDate