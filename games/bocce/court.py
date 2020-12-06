class Court:
	def __init__(self, name, orientation="north-south"):
		self.name = name
		self.orientation = orientation
		self.birdseyeCams = []
		self.playerCams = []
		self.game = None

	def add_birdseye_cam(self, cam):
		self.birdseyeCams.append(cam)

	def remove_birdseye_cam(self, cam):
		pass

	def add_player_cam(self, cam):
		self.playerCams.append(cam)

	def remove_player_cam(self, cam):
		pass

	def set_game(self, game):
		self.game = game
		self.game.orientation = self.orientation

	def end_game(self):
		self.game = None

	def __str__(self):
		return "{}: {} ({})".format(self.__class__.__name__, self.name,
			self.orientation)

