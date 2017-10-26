import statistics
import espnff


class League:
    name = ""
    num_teams = 0
    num_playoff_teams = 0
    tie_rule = ""
    seed_tiebreaker = ""
    num_regular_season_matchups = 0
    divisions = {}  # key is divID and value is division name
    teams = {}  # key is teamID and value is team name

    def __init__(self, name, num_teams, num_playoff_teams, tie_rule, seed_tiebreaker, num_regular_season_matchups,
                 divisions=None, teams=None, results=None):
        if divisions is None:
            divisions = {}
        if teams is None:
            teams = {}
        self.name = name
        self.num_teams = num_teams
        self.num_playoff_teams = num_playoff_teams
        self.tie_rule = tie_rule
        self.seed_tiebreaker = seed_tiebreaker
        self.num_regular_season_matchups = num_regular_season_matchups
        self.divisions = divisions
        self.teams = teams
        self.results = results


class Team:
    def __init__(self, name, owner, id, div_id, points_for, points_against, wins, losses, schedule=None,
                 points_by_week=None):
        if schedule is None:
            schedule = []
        if points_by_week is None:
            points_by_week = []
        self.name = name
        self.owner = owner
        self.id = id
        self.div_id = div_id
        self.points_for = points_for
        self.points_against = points_against
        self.wins = wins
        self.losses = losses
        self.schedule = schedule
        self.points_by_week = points_by_week
        self.std_dev = self.calculate_std_dev()

    def __str__(self):
        return self.name + ", " + self.owner + " (" + str(self.wins) + "-" + str(self.losses) + ")"

    def calculate_std_dev(self):
        if len(self.points_by_week) > 2:
            return statistics.pstdev(self.points_by_week)

    # def statistics_as_of_week(self, week):
            # TODO: Allow for calculation of metrics by week


def initialize(league_id, year):
    league_data = espnff.League(league_id, year)
    name = league_data.settings.name
    num_teams = league_data.settings.team_count
    num_playoff_teams = league_data.settings.playoff_team_count
    tie_rule = league_data.settings.tie_rule
    seed_tiebreaker = league_data.settings.playoff_seed_tie_rule
    num_regular_season_matchups = league_data.settings.reg_season_count
    divisions = {}  # key is divID and value is division name
    team_names = {}  # key is teamID and value is team name
    team_instances = {}  # key is teamId and value is Team obj

    league_results = {}

    for i in range(league_data.settings.reg_season_count):
        scoreboard = league_data.scoreboard(i)
        for matchup in scoreboard:
            league_results['homeTeam'] = matchup.home_team
            league_results['homeScore'] = matchup.home_score
            league_results['awayTeam'] = matchup.away_team
            league_results['awayScore'] = matchup.away_score

    for tm in league_data.teams:
        team_names[tm.team_id] = tm.team_name
        divisions[tm.division_id] = tm.division_name
        team_instances[tm.team_id] = Team(tm.team_name, tm.owner, tm.team_id, tm.division_id, tm.points_for,
                                          tm.points_against, tm.wins, tm.losses, tm.schedule, tm.scores)

    league_instance = League(name, num_teams, num_playoff_teams, tie_rule, seed_tiebreaker, num_regular_season_matchups,
                             divisions, team_names, league_results)
    return league_instance, team_instances


league, teams = initialize(2253602, 2017)

for key, val in teams.items():
    print(val, val.points_for, val.std_dev)