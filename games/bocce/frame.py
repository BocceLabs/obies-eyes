# imports
from .ball import Pallino
from .throw import Throw
from .cv.ballfinder import BallFinder
from scipy.spatial import distance as dist


# for now, these are "pixels" (not "inches" or "cm")
TOO_CLOSE_MARGIN = 5

class Frame:
    def __init__(self, frameNumber, throwingEnd, pallinoThrowingTeam,
        teamHome, teamAway, cam):

        self.frameNumer = frameNumber
        self.throwingEnd = throwingEnd
        self.frameWinner = None

        self.pallinoThrowingTeam = pallinoThrowingTeam
        self.teamHome = teamHome
        self.teamAway = teamAway

        # todo
        self.cam = cam

        self.pallinoInPlay = False
        self.ballMotion = False
        self.whoseIn = None
        self.inPoints = 0
        self.framePoints = 0

        #### throws ####
        self.throw = None
        self.throws = []
        self.first_bocce_thrown = False
        self.second_bocce_thrown = False
        self.numThrowsTeamHome = 0
        self.numThrowsTeamAway = 0

        self.throw_trigger = False

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

    def start(self):
        print("Frame {} is started".format(str(self.frameNumer)))

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

    def increment_team_throw_count(self, team):
        if team == self.teamHome:
            self.numThrowsTeamHome += 1
        elif team == self.teamAway:
            self.numThrowsTeamAway += 1

    def throw_bocce(self, team, followPallino=False):
        thrower = None

        # whichever team threw the pallino throws again
        if followPallino:
            print("Following the pallino")
            team = self.pallinoThrowingTeam

        # otherwise, it is the furthest team's throw
        else:
            # if the furthest team has no more balls, then switch teams
            if self.get_num_remaining_team_balls(team) <= 0:
                # switch team
                team = self.get_other_team(team)

        # grab a bocce ball from the team
        ball = self.get_a_team_ball(team.balls)

        # grab a player from the team
        # todo: determine the throwing player; currently gets a random player with ball
        thrower = team.get_random_player_with_balls()

        # throw the bocce ball
        ball.set_thrower(thrower)
        self.throw = Throw(thrower, ball)
        self.throw.throw()
        self.increment_team_throw_count(team)
        valid = self.throw.valid

        # update who is in
        if followPallino:
            self.whoseIn = self.get_other_team(self.pallinoThrowingTeam)
        else:
            self.whoseIn = self.determine_whose_in(self.cam.last_frame)

        # debug
        print("{}({}) threw a bocce. Throw is {}. {} is in with points={}. {} remaining balls={}".format(
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

    def handle_throw(self):
        if not self.pallino.isThrown:
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
                return
            return

        # the pallino thrower NEEDS to throw their first ball
        if not self.first_bocce_thrown:
            self.throw_bocce(self.pallinoThrowingTeam,
                             followPallino=True)
            self.first_bocce_thrown = True
            self.update_in_points(1) # force to one point
            self.first_bocce_thrown = True
            return

        # the other team ALWAYS throws their first ball next
        if not self.second_bocce_thrown:
            print("The other team ALWAYS throws their first ball next")
            self.throw_bocce(self.get_other_team(self.pallinoThrowingTeam), followPallino=False)
            self.second_bocce_thrown = True
            # todo we need to determine who is in but kmeans fails if all dff ball nums = 1
            self.update_in_points(1)
            return

        else:
            if self.either_team_has_balls():
                # throw all remaining balls
                self.inPoints, self.whoseIn = self.determine_whose_in(self.cam)

                # the other team (furthest team) throws
                valid = self.throw_bocce(self.get_other_team(self.whoseIn),
                                             followPallino=False)

            else:
                print("Please score the frame")
                # if we reach this, then the frame is done, so cleanup
                self.set_frame_points(self.whoseIn, self.inPoints)

    def get_other_team(self, team):
        if team == self.teamHome:
            return  self.teamAway
        return self.teamHome

    """Finds closest ball with computer vision"""
    def determine_whose_in(self, court):
        bf = BallFinder()
        bf.pipeline(court, self.numThrowsTeamHome, self.numThrowsTeamAway)
        self.pallino = bf.pallino
        self.teamHome.balls = bf.homeBalls
        self.teamAway.balls = bf.awayBalls

        points, frameLeader = self.get_frame_points_and_frame_leader(self.pallino, self.teamHome.balls,
            self.teamAway.balls)

        return points, frameLeader


    def get_frame_points_and_frame_leader(self, pallino, homeBalls, awayBalls):
        def get_frame_points(ballDistancesA, ballDistancesB):
            framePoints = 0
            for (i, dB) in enumerate(ballDistancesB):
                for (j, dA) in enumerate(ballDistancesA):
                    if dA < dB:
                        framePoints += 1
                    else:
                        break
                break
            return framePoints


        if pallino is None:
            print("not annotating; couldn't find pallino")

        # calculate Euclidean distance for each ball to the pallino
        homeBallsDistances = []
        awayBallsDistances = []
        for ball in homeBalls:
            D = dist.euclidean(pallino.coordinates, ball.coordinates)
            homeBallsDistances.append(D)
        for ball in awayBalls:
            D = dist.euclidean(pallino.coordinates, ball.coordinates)
            awayBallsDistances.append(D)

        # sort balls and distances
        homeBallsDistances, homeBalls = zip(*sorted(zip(homeBallsDistances, homeBalls)))
        awayBallsDistances, awayBalls = zip(*sorted(zip(awayBallsDistances, awayBalls)))

        # grab each min distance (the 0th element in the sorted list)
        homeBallsMinDistance = homeBallsDistances[0]
        awayBallsMinDistance = awayBallsDistances[0]

        # who is closer?
        homeIsCloser = homeBallsMinDistance < awayBallsMinDistance
        awayIsCloser = awayBallsMinDistance < homeBallsMinDistance
        equidistant = homeBallsMinDistance == awayBallsMinDistance

        # check if it is "too close to call"
        tooCloseToCall = abs(homeBallsMinDistance - awayBallsMinDistance) <= TOO_CLOSE_MARGIN

        # determine framePoints and frameWinner
        framePoints = None
        frameLeader = None
        if homeIsCloser:
            framePoints = get_frame_points(homeBallsDistances, awayBallsDistances)
            frameLeader = self.teamHome
        elif awayIsCloser:
            framePoints = get_frame_points(awayBallsDistances, homeBallsDistances)
            frameLeader = self.teamAway
        elif equidistant or tooCloseToCall:
            # todo how do we handle when both teams' closest ball is equidistant
            framePoints = None

        return framePoints, frameLeader


    """Determine's who is in and accounts for their points"""
    def update_in_points(self, points=None):
        # determine who is in
        if points is not None:
            self.inPoints = points
            return

        # check for balls closest to pallino
        ballsThrown = 1 + self.numThrowsTeamHome + self.numThrowsTeamAway

        # if at least two bocce balls are thrown
        if ballsThrown >= 2:
            self.inPoints, self.whoseIn = self.determine_whose_in(self.cam.last_frame)
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