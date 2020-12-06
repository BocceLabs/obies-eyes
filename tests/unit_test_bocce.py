# imports
import sys
import os

# add the parent directory (absolute, not relative) to the sys.path
# (this makes the games package imports work)
sys.path.append(os.path.abspath(os.pardir))

# imports
from games.bocce.venue import Venue
from games.bocce.court import Court
from games.bocce.team import Team
from games.bocce.person import Player, Umpire
from games.bocce.throw import Throw
from games.bocce.frame import Frame
from games.bocce.game import Game
from games.camera.camera import USBCamera, RTSPCamera, PubSubImageZMQCamera

# create a venue
print("\n[INFO] Creating a venue...")
v = Venue("Bridge 410")
print(str(v))

# create courts
print("\n[INFO] Creating three courts...")
cFence = Court("Fence", "north-south")
cMiddle = Court("Middle", "north-south")
cSidewalk = Court("Sidewalk", "north-south")
print(str(cFence))
print(str(cMiddle))
print(str(cSidewalk))

# add courts to the venue
v.add_court(cFence)
v.add_court(cMiddle)
v.add_court(cSidewalk)

# print the venue string
print("\n[INFO] Checking to see if the venue has courts...")
print(str(v) + ": " + v.str_courts())

# add cameras to the sidewalk court
print("\n[INFO] Creating two cameras and assigning them to a court...")
camA = USBCamera(name="SidewalkA", source=0)
camB = USBCamera(name="SidewalkB", source=1)
print(str(camA))
print(str(camB))
camA.initialize()
camB.initialize()
cSidewalk.add_birdseye_cam(camA)
cSidewalk.add_birdseye_cam(camB)

# grab a couple frames from the cameras
print("\n[INFO] Grabbing camera frames to ensure they are working...")
camA.get_frame()
camB.get_frame()
print(".....success")

# create some players
print("\n[INFO] Creating four players...")
playerDH = Player("David Hoffman", "david.r.hoffman@ieee.org")
playerEH = Player("Elizabeth Hoffman", "edias014@gmail.com")
playerMD = Player("Matt David", "matt@americanbocceco.com")
playerAG = Player("Alex Gara", "alex@americanbocceco.com")
print(str(playerDH))
print(str(playerEH))
print(str(playerMD))
print(str(playerAG))

# create a team
print("\n[INFO] Creating two teams and adding players...")
teamA = Team("J.K. Rollin'")
teamA.add_player(playerDH)
teamA.add_player(playerEH)
teamA.set_team_ball_color("red")
teamB = Team("Bocce Kings")
teamB.add_player(playerMD)
teamB.add_player(playerAG)
teamB.set_team_ball_color("blue")
print(str(teamA))
print(str(teamB))

# create a game
# a game consists of (a) umpire, (b) home team, (c) away team
print("\n[INFO] Setting up a death match...")
u = Umpire("Alicia", "alicia@americanbocceco.com")
g = Game(umpire=u, teamHome=teamB, teamAway=teamA)
print(str(g))

# start the game
print("\n[INFO] Starting the game...")
cSidewalk.set_game(g)
print("\n[INFO] Game is being played at {} on {}...".format(str(v), str(cSidewalk)))
g.start()
print("[INFO] Game is started; clock is set...\n")
g.game_runner()