
courtLength = 30

class Throw:
	def __init__(self, player, ball):
		self.player = player
		self.ball = ball

		self.valid = None

		# punto, raffa, vollo
		self.throwType = None

		self.thrown = None
		self.crossedMidCourtLine = None
		self.hitBackWall = None

	def throw(self):
		# mark the ball as thrown
		self.thrown = True
		self.ball.isThrown = True
		self.player.throw()

		# todo: eliminate this OVERRIDE that marks the ball as valid
		self.valid = True
		return self.valid

		# while self.ball.is_moving():
		# 	# grab the y coordinate
		# 	y = self.ball.currentCoords[1]
		#
		# 	# midcourt is y=0 based on coordinate system
		# 	if y >= 0:
		# 		self.crossedMidCourtLine = True
		#
		# 	# determine if the ball hit the back wall without touching
		# 	# another ball
		# 	if not self.ball.contactedAnotherBall:
		# 		if y < courtLength / 2:
		# 			self.hitBackWall = False
		#
		# # ball is no-longer moving
		# if self.crossedMidCourtLine and not self.hitBackWall:
		# 	self.valid = True
		#
		# # invalid balls are removed (or in the case of the pallino are
		# # thrown by the next team)
		# else:
		# 	self.valid = False
		#
		#
		# return self.valid
