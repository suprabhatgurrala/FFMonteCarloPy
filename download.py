import urllib.request

import re
from bs4 import BeautifulSoup


def get_soup(url):
    """
    Retrieve a URL
    :param url:
    :return:
    """
    r = urllib.request.urlopen(url).read()
    return BeautifulSoup(r, "html.parser")


def get_league_schedule(league_id, season, num_matchup_periods):
    """
    Get the league schedule for the specified season
    :param league_id: ESPN.com league ID
    :param season: specified season to get the schedule
    :return: a dict of the schedule with week number as the key and the matchup as the value
    """
    schedule_dict = {}
    for matchupId in range(num_matchup_periods):
        url = "http://games.espn.com/ffl/scoreboard?leagueId=" + str(league_id) + "&seasonId=" + str(
            season) + "&matchupPeriodId=" + str(matchupId + 1)
        soup = get_soup(url)
        scoreboard_div = soup.find('div', id="scoreboardMatchups")
        matchups = scoreboard_div.findAll('table', {'class': "ptsBased matchup"})
        for matchup in matchups:
            home_team_name = ""
            away_team_name = ""
            home_score = None
            away_score = None
            home_abbr = matchup.find('td', {'class', "homeTeam abbrev"}).text
            team_abbrs = matchup.findAll('span', {'class': "abbrev"})
            if home_abbr in team_abbrs[0]:
                home_index = 0
                away_index = 1
            else:
                home_index = 1
                away_index = 0

            home_team_name = matchup.findAll('div', {'class': "name"})[home_index].text
            home_team_score_element = matchup.findAll('td', {'class': re.compile("score")})[home_index].get('title')
            home_score = float(home_team_score_element)

            away_team_name = matchup.findAll('div', {'class': "name"})[away_index].text
            away_team_score_element = matchup.findAll('td', {'class': re.compile("score")})[away_index].get('title')
            away_score = float(away_team_score_element)

            # TODO: Consider the best way to store schedule data.
            matchup_dict = {}

            break
        schedule_dict = {}
        break
    return schedule_dict


def get_league_settings(league_id, season):
    """
    Get metadata about the league i.e. divisions, schedule length, tiebreakers, etc.
    :param league_id: ESPN.com league ID
    :param season: specified season to get the settings
    :return: a dict with relevant league settings
    """
    url = "http://games.espn.com/ffl/leaguesetup/settings?leagueId=" + str(league_id) + "&seasonId=" + str(season)
    soup = get_soup(url)
    settings_dict = {}

    # Extract basic league settings
    settings_div = soup.find('div', id="settings-content")
    basic_settings_table = settings_div.find('table', id="basicSettingsTable")
    basic_settings_rows = basic_settings_table.findAll('tr', attrs={"class": re.compile("row")})
    for row in basic_settings_rows:
        label = row.find("label")
        cols = row.findAll("td")
        if label:
            text = cols[1].text
            if text.isdigit():
                text = int(text)
            settings_dict[label.get("for")] = text

    # Extract divisions
    team_division_settings_table = settings_div.find('div', {'name': 'teaminfo'})
    team_division_rows = team_division_settings_table.findAll('tr', attrs={"class": re.compile("row")})
    settings_dict['numDivisions'] = len(team_division_rows)
    settings_dict['divisions'] = {}
    for row in team_division_rows:
        name = row.find('td').text
        teams = []
        for col in row.find_all('td', width="50%"):
            teams.append(col.text)
        settings_dict['divisions'][name] = teams

    # Extract regular season schedule settings
    regular_season_setup_table = settings_div.find('div', {'class': "regularSeasonSettings"})
    reg_season_matchups_text = regular_season_setup_table.find("label", {
        'for': "regularSeasonMatchupPeriodCount"}).parent.next_sibling.text
    search = re.search("([0-9]*) ", reg_season_matchups_text)
    num_reg_season_matchups = int(search.group(1)) if search else None
    settings_dict['regularSeasonMatchups'] = num_reg_season_matchups

    reg_season_tiebreak_text = regular_season_setup_table.find('label', {'for': "tieRule"}).parent.next_sibling.text
    settings_dict['regularSeasonTiebreak'] = reg_season_tiebreak_text

    # Extract playoff settings
    playoff_settings_table = settings_div.find('div', {'class': "playoffSettings"})
    num_playoff_teams_text = playoff_settings_table.find("label", {'for': "playoffTeamCount"}).parent.next_sibling.text
    search = re.search("([0-9]*) \(", num_playoff_teams_text)
    num_playoff_teams = int(search.group(1)) if search else None
    settings_dict['playoffTeams'] = num_playoff_teams

    seeding_tiebreak_text = playoff_settings_table.find("label",
                                                        {'for': "playoffSeedingTieRule"}).parent.next_sibling.text
    settings_dict['seedTiebreak'] = seeding_tiebreak_text

    return settings_dict



print(get_league_schedule(565232, 2017, 13))
