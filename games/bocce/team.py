# imports
from .ball import Bocce

class Team:
	def __init__(self, teamName):
		self.players = []
		self.teamName = teamName
		self.teamBallColor = None
		self.balls = []

	def add_player(self, player):
		if len(self.players) < 4:
			self.players.append(player)
		else:
			raise ValueError("Max players for team is already reached")

	def remove_player(self, player):
		# todo
		pass

	def set_team_ball_color(self, color):
		self.teamBallColor = color

	def add_balls(self, qty):
		# 2 balls for the single player on the team
		if qty == 2 and len(self.players) == 1:
			for p in self.players:
				p.initialize_throw_count(2)

		# 2 balls for each of the 2 players on the team
		elif qty == 4 and len(self.players) == 2:
			for p in self.players:
				p.initialize_throw_count(2)

		# 1 ball for each of the 4 players on the team
		elif qty == 4 and len(self.players) == 4:
			for p in self.players:
				p.initialize_throw_count(1)

		while qty > 0:
			self.balls.append(Bocce(self.teamBallColor))
			qty -= 1

	def get_random_player(self):
		import random
		randomPlayer = self.players[random.randint(0, len(self.players) - 1)]
		return randomPlayer

	def get_random_player_with_balls(self):
		# todo implement without random
		while True:
			p = self.get_random_player()
			if p.throwCount >= 0:
				return p
			else:
				continue

	def str_players(self):
		output = self.teamName + " (" + self.teamBallColor + "): "
		for player in self.players:
			output += player.name + ", "
		return output[:-2]

	def __str__(self):
		return "{}: {}".format(self.__class__.__name__, self.teamName)

