import datetime
import statistics
from collections import OrderedDict
from pprint import pprint

import numpy
import copy

import scipy.stats

import download

OUTCOME_TBD = 0
OUTCOME_HOME_WIN = 1
OUTCOME_AWAY_WIN = 2
OUTCOME_TIE = 3

TIEBREAK_H2H = 0
TIEBREAK_PF = 1
TIEBREAK_DIV = 2
TIEBREAK_PA = 3

NUMBER_OF_SIMULATIONS = 1000
CURRENT_YEAR = datetime.datetime.now().year

class League:
    def __init__(self, league_id, year=CURRENT_YEAR, week=None):
        league, teams, schedule_df = download.get_data(league_id, year)
        if week is None:
            self.week = league['current_period']
        else:
            self.week = week
        self.league_info = league
        self.team_info = teams
        self.schedule_df = schedule_df
        self.schedule_as_of_week = self.init_schedule_as_of_week()
        self.team_stats = {}
        for tm_id, tm in teams.items():
            self.team_stats[tm_id] = {}
        self.init_stats()
        self.init_probabilities()
        self.league_info['div_members'] = self.init_div_members()

    def init_div_members(self):
        """
        Initialization method to be run in __init__()
        :return: a dict with division IDs as keys and the teams in that division as values
        """
        div_members = {}
        for d_id, name in self.league_info.get('divisions').items():
            div_members[d_id] = []

        for tm_id, tm in self.team_info.items():
            div_members[tm.get('div_id')].append(tm_id)
        return div_members

    def init_schedule_as_of_week(self):
        return self.schedule_df[self.schedule_df.week < self.week]

    def init_stats(self):
        """
        Calculates teams' stats. Initialization method to be run in __init__().
        :return: does not return anything, modifies the team_stats dict
        """
        for id, tm in self.team_info.items():
            home_games = self.schedule_as_of_week[self.schedule_as_of_week.home_id == id]
            away_games = self.schedule_as_of_week[self.schedule_as_of_week.away_id == id]
            self.team_stats[id]['wins'] = len(home_games[home_games.outcome == OUTCOME_HOME_WIN]) + len(
                away_games[away_games.outcome == OUTCOME_AWAY_WIN])
            self.team_stats[id]['losses'] = len(home_games[home_games.outcome == OUTCOME_AWAY_WIN]) + len(
                away_games[away_games.outcome == OUTCOME_HOME_WIN])
            self.team_stats[id]['ties'] = len(home_games[home_games.outcome == OUTCOME_TIE]) + len(
                away_games[away_games.outcome == OUTCOME_TIE])

            points_for_list = list(home_games.home_score) + list(away_games.away_score)
            points_against_list = list(home_games.away_score) + list(away_games.home_score)

            self.team_stats[id]['average'] = statistics.mean(points_for_list)
            self.team_stats[id]['std_dev'] = statistics.pstdev(points_for_list) if self.week > 2 else None
            self.team_stats[id]['points_for'] = sum(points_for_list)
            self.team_stats[id]['points_against'] = sum(points_against_list)

    def init_probabilities(self):
        """
        Calculates win probabilities for each matchup in the schedule. Initialization method to be run in __init__()
        """
        for row_index, row in self.schedule_df.iterrows():
            if row.home_id != -1 and row.away_id != -1:
                home_average = self.team_stats[row.home_id]['average']
                home_std_dev = self.team_stats[row.home_id]['std_dev']
                away_average = self.team_stats[row.away_id]['average']
                away_std_dev = self.team_stats[row.away_id]['std_dev']
                mean = home_average - away_average
                std_dev = numpy.sqrt(home_std_dev ** 2 + away_std_dev ** 2)
                self.schedule_df.loc[row_index, 'probability'] = 1 - scipy.stats.norm.cdf(0, loc=mean, scale=std_dev)
            else:
                self.schedule_df.loc[row_index, 'probability'] = 0

        self.schedule_as_of_week = self.init_schedule_as_of_week()
        for tm_id, tm in self.team_stats.items():
            home_probs = self.schedule_as_of_week[self.schedule_as_of_week.home_id == tm_id]['probability']
            away_probs = self.schedule_as_of_week[self.schedule_as_of_week.away_id == tm_id]['probability']
            expected_wins = sum(home_probs)
            for away_prob in away_probs:
                expected_wins += 1 - away_prob
            tm['expected_wins'] = expected_wins

    def calculate_standings(self):
        """
        Generates standings
        :return: a list of team IDs ordered by playoff seed (e.g. item at index 0 is #1 overall seed etc.)
        """

        # Group teams by record
        # wins_dict = {}
        # for tm_id, tm in self.team_stats.items():
        #     if wins_dict.get(tm['wins']) is not None:
        #         wins_dict[tm['wins']].append(tm_id)
        #     else:
        #         wins_dict[tm['wins']] = [tm_id]
        # wins_dict_ordered = OrderedDict(sorted(wins_dict.items(), reverse=True))
        record_dict = {}
        for tm_id, tm in self.team_stats.items():
            record = tm['wins'], tm['losses'], tm['ties']
            if record_dict.get(record) is not None:
                record_dict[record].append(tm_id)
            else:
                record_dict[record] = [tm_id]
        sorted_records = sorted(record_dict, key=self.__get_win_percentage, reverse=True)

        standings = []
        for record in sorted_records:
            tied_team_ids = record_dict.get(record)
            ordered = []
            while len(tied_team_ids) > 1:
                tie_winner = self.tiebreak(tied_team_ids)
                ordered.append(tie_winner)
                tied_team_ids.remove(tie_winner)
            ordered.append(tied_team_ids[0])
            standings += ordered

        # promote division winner(s)
        first_seed = standings.pop(0)
        div_winners = [first_seed]
        div_ids = list(self.league_info['divisions'].keys())
        div_ids.remove(self.team_info.get(first_seed).get('div_id'))
        # Find remaining division winners and pull them out in place.
        for tm in standings:
            if len(div_ids) > 0:
                tm_div_id = self.team_info.get(tm).get('div_id')
                if tm_div_id in div_ids:
                    div_winners.append(tm)
                    div_ids.remove(tm_div_id)
                    standings.remove(tm)
            else:
                break
        return div_winners + standings

    def tiebreak(self, tied_teams):
        """
        :param tied_teams: team_ids of the teams with tied records
        :return: the team id of the team that wins the tiebreak
        """
        tiebreak_method = self.league_info.get('seed_tiebreaker')

        # Copying tied_teams list to prevent interference with outside manipulation of tied_teams
        tied_teams_copy = copy.deepcopy(tied_teams)

        if tiebreak_method == TIEBREAK_H2H:
            tie_winner = self.tiebreak_h2h(tied_teams_copy)
        elif tiebreak_method == TIEBREAK_DIV:
            tie_winner = self.tiebreak_div(tied_teams_copy)
        elif tiebreak_method == TIEBREAK_PA:
            tie_winner = self.tiebreak_pa(tied_teams_copy)
        else:
            # If none of the other tiebreakers were applicable, use total points for as tiebreaker
            tied_teams_copy.sort(key=self.__get_pf, reverse=True)
            tie_winner = tied_teams[0]
        return tie_winner

    def __get_pf(self, team_id):
        """
        Helper function for sorting
        :param team_id
        :return: total points scored by the specified team
        """
        return self.team_stats.get(team_id, {}).get('points_for')

    def __get_pa(self, team_id):
        """
        Helper function for sorting
        :param team_id
        :return: total points that have been scored against the specified team
        """
        return self.team_stats.get(team_id, {}).get('points_against')

    def __get_win_percentage(self, record):
        """
        Calculates win percentage of a given record
        :param record: tuple of form (wins, losses, ties)
        :return: win percentage
        """
        wins, losses, ties = record
        return (wins + ties * 0.5) / (wins + losses + ties)

    def __get_div_win(self, team_id):
        """
        Helper function for sorting
        :param team_id:
        :return: Intra-division win percentage for the specified team
        """
        division = self.team_info.get(team_id).get('div_id')
        div_members = self.league_info.get('div_members').get(division, [])

        wins = 0
        games_played = 0

        div_home_games = self.schedule_as_of_week[
            (self.schedule_as_of_week.home_id == team_id) & (self.schedule_as_of_week.away_id.isin(div_members))
        ]

        for row_index, row in div_home_games.iterrows():
            if row.outcome == OUTCOME_HOME_WIN:
                wins += 1
            elif row.outcome == OUTCOME_TIE:
                wins += 0.5
            games_played += 1

        div_away_games = self.schedule_as_of_week[
            (self.schedule_as_of_week.away_id == team_id) & (self.schedule_as_of_week.home_id.isin(div_members))
            ]

        for row_index, row in div_away_games.iterrows():
            if row.outcome == OUTCOME_AWAY_WIN:
                wins += 1
            elif row.outcome == OUTCOME_TIE:
                wins += 0.5
            games_played += 1

        return wins * 1.0 / games_played

    def tiebreak_h2h(self, tied_teams):
        # calculate H2H records for all teams involved in tie
        # H2H only applies if all teams have same number of games played against each other
        # Total points for is secondary tiebreaker
        h2h_results = {}
        for tm in tied_teams:
            h2h_results[tm] = {'team_id': tm, 'wins': 0, 'games': 0, 'pf': self.__get_pf(tm)}

            h2h_home_games = self.schedule_as_of_week[
                (self.schedule_as_of_week.home_id == tm) & (self.schedule_as_of_week.away_id.isin(tied_teams))
                ]

            for row_index, row in h2h_home_games.iterrows():
                if row.outcome == OUTCOME_HOME_WIN:
                    h2h_results[tm]['wins'] += 1
                elif row.outcome == OUTCOME_TIE:
                    h2h_results[tm]['wins'] += 0.5
                h2h_results[tm]['games'] += 1

            h2h_away_games = self.schedule_as_of_week[
                (self.schedule_as_of_week.away_id == tm) & (self.schedule_as_of_week.home_id.isin(tied_teams))
                ]

            for row_index, row in h2h_away_games.iterrows():
                if row.outcome == OUTCOME_AWAY_WIN:
                    h2h_results[tm]['wins'] += 1
                elif row.outcome == OUTCOME_TIE:
                    h2h_results[tm]['wins'] += 0.5
                h2h_results[tm]['games'] += 1

        num_h2h_games = h2h_results[tied_teams[0]]['games']
        # Sort by secondary tiebreaker
        h2h_ordered = sorted(h2h_results.values(), key=lambda val: val['pf'], reverse=True)
        if all(value['games'] == num_h2h_games for value in h2h_results.values()):
            # Teams have played the same number of H2H games, tiebreaker is applicable.
            h2h_ordered.sort(key=lambda val: val['wins'], reverse=True)
        return h2h_ordered[0]['team_id']

    def tiebreak_pa(self, tied_teams):
        # H2H record is secondary tiebreaker
        ordered = []
        while len(tied_teams) > 1:
            tie_winner = self.tiebreak_h2h(tied_teams)
            ordered.append(tie_winner)
            tied_teams.remove(tie_winner)
        ordered.append(tied_teams[0])

        # Team with more points against is considered superior
        ordered.sort(key=self.__get_pa, reverse=True)

        return ordered[0]

    def tiebreak_div(self, tied_teams):
        # H2H record is secondary tiebreaker
        ordered = []
        while len(tied_teams) > 1:
            tie_winner = self.tiebreak_h2h(tied_teams)
            ordered.append(tie_winner)
            tied_teams.remove(tie_winner)
        ordered.append(tied_teams[0])

        # Team with highest division win percentage is superior
        ordered.sort(key=self.__get_div_win, reverse=True)

        return ordered[0]


league = League(2253602, week=12)
print(league.calculate_standings())
