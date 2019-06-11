

class GlucoseEffect:
	def __init__ (self, startDate, quantity):
		self.startDate = startDate
        self.quantity = quantity

    def __ls__ (self, other):
    	return self.startDate < other.startDate