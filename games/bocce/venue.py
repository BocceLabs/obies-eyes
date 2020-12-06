class Venue():
	def __init__(self, name):
		self.name = name
		self.courts = []

	def add_court(self, court):
		self.courts.append(court)

	def remove_court(self, court):
		# todo feature to remove court
		pass

	def str_courts(self):
		# build a comma separated listing of courts and then remove
		# the last ", "
		courts_csv = ""
		for c in self.courts:
			courts_csv += c.name + ", "
		courts_csv = courts_csv[:-2]
		return "Courts: {}".format(courts_csv)

	def __str__(self):
		return "{}: {}".format(self.__class__.__name__, self.name)

