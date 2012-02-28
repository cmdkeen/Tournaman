import os
import xml.etree.ElementTree as ET

class Tournament:
    venues_file = "venues%d-main.dat" #Doesn't create an XML file for this
    debate_file = "debates%d-main.xml"
    teams_file = "teams%d-main.xml"
    judges_file = "adjudicators%d-main.xml"

    def __init__(self):
        self.rounds = dict()
        self.teams = dict()
        self.judges = dict()
        self.venues = dict()

    def sorted_teams(self):
        x = sorted(self.teams.values(), reverse=True, key=lambda t: t.speaks())
        return sorted(x, reverse=True, key=lambda t: t.total())

    def load_directory(self, directory):
        venues = []
        rounds = []
        teams = []
        judges = []

        i = 1
        while os.path.exists(os.path.join(directory, (self.debate_file % i))): #Debates may lag behind the other files as it is created for a draw
            venues.append((i,os.path.join(directory, (self.venues_file % i))))
            rounds.append((i,os.path.join(directory, (self.debate_file % i))))
            teams.append(os.path.join(directory, (self.teams_file % i)))
            judges.append(os.path.join(directory, (self.judges_file % i)))
            i += 1

        if i == 1:
            print "No files found"
            return

        for i, loc in venues:
            self._read_venue(i, loc)

        self._read_judges(judges[-1])
        self._read_teams(teams[-1])

        for i, loc in rounds:
            self._read_round(i, loc)

    def _read_venue(self, number, location):
        f = open(location, "r")
        self.venues[number] = [x.split(" ")[1]  for x in f.readlines()]

    def _read_judges(self, location):
        tree = ET.parse(location)

        judges = [(int(x.get("id")), x.get("name")) for x in tree.getroot().getchildren()]
        for id, name in judges:
            self.judges[id] = Judge(name)

    #TODO look into speakers changing between rounds
    def _read_teams(self, location):
        tree = ET.parse(location)

        for el in tree.findall("team"):
            t = Team(el.get("name"))
            self.teams[int(el.get("ident"))] = t
            home = el.find("home")
            pullups = el.find("pullups")
            if home is not None:
                t.home = home.text
            if pullups is not None:
                t.pullups = pullups
            speakers = [Speaker(x.get("name"), t) for x in el.findall("member")]
            for i, s in enumerate(speakers):
                t.speakers[i] = s

    def _read_round(self, number, location):
        tree = ET.parse(location)
        self.rounds[number] = round = Round(number)

        motion = tree.find("motion")
        judges = tree.find("adjudicators")

        if motion is not None:
            round.motion = motion.text

        for el in tree.findall("debate"):
            vid = int(el.get("venue"))
            round.debates[vid] = debate = Debate(round, self.venues[number][vid])

            for i, tel in enumerate(el.findall("team")):
                t = self.teams[int(tel.get("id"))]
                t.debates[number] = debate
                t.positions[number] = i
                t.scores[number] = int(tel.get("rankpts"))
                debate.positions[i] = t

                for id, points in [(int(x.get("id")), int(x.get("points"))) for x in tel.findall("speaker")]:
                    t.speakers[id].debates[number] = debate
                    t.speakers[id].scores[number] = points

        if judges is not None:
            map = [(int(x.get("adj")), int(x.get("venue"))) for x in judges.getchildren()]
            for j, v in map:
                self.judges[j].debates[number] = round.debates[v]

class Round:
    def __init__(self, number):
        self.number = number
        self.debates = dict()
        self.motion = None

    def __str__(self):
        return "Round %d: %s" % (self.number, self.motion)

class Speaker:
    def __init__(self, name, team):
        self.name = name
        self.team = team
        self.debates = dict()
        self.scores = dict()

    def __str__(self):
        return self.name

    def total(self):
        return sum(self.scores.values())

class Team:
    def __init__(self, name):
        self.name = name
        self.speakers = dict()
        self.debates = dict()
        self.pullups = None
        self.positions = dict()
        self.scores = dict()

    def __str__(self):
        return self.name

    def total(self):
        return sum(self.scores.values())

    def speaks(self):
        return sum([s.total() for s in self.speakers.values()])

class Judge:
    def __init__(self, name):
        self.name = name
        self.debates = dict()

    def __str__(self):
        return self.name

class Debate:
    def __init__(self, round, venue):
        self.round = round
        self.positions = dict()
        self.judges = []
        self.venue = venue