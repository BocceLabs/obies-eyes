class Person:
	def __init__(self, name, email):
		self.name = name
		self.email = email

	def __str__(self):
		return "{}: {}".format(self.__class__.__name__, self.name)

class Umpire(Person):
	pass

class Player(Person):
	def __init__(self, name, email):
		self.name = name
		self.email = email
		self.throwCount = None

	def initialize_throw_count(self, throws):
		self.throwCount = throws

	def throw(self):
		self.throwCount -= 1
