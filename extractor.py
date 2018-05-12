import urllib.parse as urlparse
import re


def extract_leagueId(url):
	try:
		parsed = urlparse.urlparse(url)
		leagueId_str = (urlparse.parse_qs(parsed.query)['leagueId'])[0] #throws KeyError
		leagueId = int(re.sub("[^0-9]", "", leagueId_str)); #throws ValueError
	except (ValueError, KeyError) as e:
		error = 'Invalid URL'
		return (False, error)
	return (True, leagueId)