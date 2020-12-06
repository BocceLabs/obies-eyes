# imports
from .ball import Pallino, Bocce
from .throw import Throw

class Frame:
	def __init__(self, frameNumber, throwingEnd, pallinoThrowingTeam,
		teamHome, teamAway):

		self.frameNumer = frameNumber
		self.throwingEnd = throwingEnd
		self.frameWinner = None

		self.pallinoThrowingTeam = pallinoThrowingTeam
		self.teamHome = teamHome
		self.teamAway = teamAway

		self.pallinoInPlay = False
		self.ballMotion = False
		self.whoseIn = None
		self.inPoints = 0
		self.framePoints = 0

		#### throws ####
		self.throw = None
		self.throws = []

		self.num_total_team_balls = None

	def initialize_balls(self, playersPerTeam):
		self.pallino = Pallino("yellow")

		if playersPerTeam == 1:
			self.num_total_team_balls = 2
			self.teamHome.add_balls(self.num_total_team_balls)
			self.teamAway.add_balls(self.num_total_team_balls)

		elif playersPerTeam == 2 or playersPerTeam == 4:
			self.num_total_team_balls = 4
			self.teamHome.add_balls(self.num_total_team_balls)
			self.teamAway.add_balls(self.num_total_team_balls)

		else:
			self.num_total_team_balls = None
			raise ValueError("valid playersPerTeam must be 1, 2, or 4")

	def throw_pallino(self, team):
		# throw the pallino
		# todo: determine throwing player; currently gets RANDOM player
		self.pallino.set_thrower(team.get_random_player())
		self.throw = Throw(self.pallino.thrownBy, self.pallino)
		self.throw.throw()
		valid = self.throw.valid

		# debug
		print("{} threw the pallino. Throw is {}.".format(
			self.pallino.thrownBy, "valid" if valid else "invalid"))


		if valid:
			self.pallino.isThrown = True
			self.pallinoInPlay = True

		return valid

	def throw_bocce(self, team, followPallino=False):
		thrower = None
		if followPallino:
			print("Following the pallino")
			ball = self.get_a_team_ball(self.pallinoThrowingTeam.balls)
			# todo determine throwing player; currently gets RANDOM
			# todo: player of the pallino throwing team with balls
			thrower = self.pallinoThrowingTeam.get_random_player_with_balls()

		else:
			if self.get_num_remaining_team_balls(team) <= 0:
				# switch team
				team = self.get_other_team(team)
			ball = self.get_a_team_ball(team.balls)
			# todo: determine the throwing player; currently defaults to player[0]
			thrower = team.get_random_player_with_balls()

		# throw the bocce
		ball.set_thrower(thrower)
		self.throw = Throw(thrower, ball)
		self.throw.throw()
		valid = self.throw.valid


		# update who is in
		if followPallino: self.whoseIn = self.get_other_team(self.pallinoThrowingTeam)
		else: self.whoseIn = self.determine_whose_in()

		# update the in points
		self.update_in_points()

		# debug
		print("{}({})\tthrew a bocce.\tThrow is {}.\t{}\tis in with points={}.\t{}\tremaining balls={}".format(
			str(thrower), team.teamBallColor,
			"valid" if valid else "invalid", self.whoseIn,
			self.inPoints, str(team), self.get_num_remaining_team_balls(team)))

		return valid

	def get_a_team_ball(self, balls):
		for ball in balls:
			# go to the next ball if this one is already thrown
			if ball.isThrown:
				continue

			else:
				# determined that this team has more balls to throw
				return ball

		# by default, the team doesn't have any more balls to throw
		return None

	def either_team_has_balls(self):
		if self.get_num_remaining_team_balls(self.teamHome) > 0 \
			or self.get_num_remaining_team_balls(self.teamAway) > 0:
			return True
		return False

	def get_num_remaining_team_balls(self, team):
		numBalls = 4
		for ball in team.balls:
			# go to the next ball if this one is already thrown
			if ball.isThrown:
				numBalls -= 1

		return numBalls

	def frame_runner(self):
		# get the pallino into play
		while not self.pallino.isThrown:
			# throw the pallino
			self.throw_pallino(self.pallinoThrowingTeam)

			# check to see if the pallino is in play
			if not self.pallinoInPlay:
				# swap pallino throwing team
				if self.pallinoThrowingTeam == self.teamHome:
					self.pallinoThrowingTeam = self.teamAway
				elif self.pallinoThrowingTeam == self.teamAway:
					self.pallinoThrowingTeam = self.teamHome

				# indicate that the pallino hasn't been thrown
				self.pallino.isThrown = False

		# the pallino thrower NEEDS to throw their first ball
		self.throw_bocce(self.pallinoThrowingTeam, followPallino=True)
		self.update_in_points(1)

		# the other team ALWAYS throws their first ball next
		print("The other team ALWAYS throws their first ball next")
		self.throw_bocce(self.get_other_team(self.pallinoThrowingTeam), followPallino=False)
		self.update_in_points(1)

		while self.either_team_has_balls():
			# throw all remaining balls
			self.whoseIn = self.determine_whose_in()

			# the other team throws
			valid = self.throw_bocce(self.get_other_team(self.whoseIn), followPallino=False)

		# if we reach this, then the frame is done, so cleanup
		self.set_frame_points(self.whoseIn, self.inPoints)

	def get_other_team(self, team):
		if team == self.teamHome:
			return  self.teamAway
		return self.teamHome

	"""Finds closest ball with computer vision"""
	def determine_whose_in(self):
		# todo: randomly chooses
		import random
		self.whoseIn = random.choice([self.teamHome, self.teamAway])
		return self.whoseIn

	"""Determine's who is in and accounts for their points"""
	def update_in_points(self, points=None):
		# determine who is in
		if points is not None:
			self.inPoints = points
			return

		# check for balls closest to pallino
		# todo: implement cv to determine in points
		ballsNotThrown = self.get_num_remaining_team_balls(self.determine_whose_in())
		ballsThrown = self.num_total_team_balls - ballsNotThrown

		if ballsThrown > 0:
			import random
			self.inPoints = random.randint(1, ballsThrown)
		else:
			self.inPoints = 0

	def set_frame_points(self, inTeam, inPoints):
		self.framePoints = inPoints
		self.frameWinner = inTeam

	def end(self):
		print("[INFO] frame winner is {} with points={}".format(
			self.frameWinner, self.framePoints))

		self.teamAway.balls = []
		self.teamHome.balls = []

		return self.frameWinner, self.framePoints