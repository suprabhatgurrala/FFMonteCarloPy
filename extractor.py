import urllib.parse as urlparse
import re

class IDError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
    def __str__(self):
    	return 'ID Error: ' + super().__str__()

class URLError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
    def __str__(self):
    	return 'URL Error: ' + super().__str__()

def extract_leagueId(input_string):
	parsed = urlparse.urlparse(input_string)
	if(bool(parsed.scheme)):
		#is a url of some sort, search if it is an espn url
		if(bool(re.search('games.espn.com', parsed.netloc))):
			# this url is an espn ffl url, try to get a leagueID from it
			try:
				leagueId_str = (urlparse.parse_qs(parsed.query)['leagueId'])[0]
				try:
					leagueId = int(leagueId_str); #throws ValueError
				except ValueError as e:
					raise URLError("League ID is invalid")
				return leagueId
			except KeyError as e:
				raise URLError("League ID could not be found")
		else:
			raise URLError("This is not an ESPN Fantasy Football URL")
	else:
	# try to see if it is just a league ID
		#if this string contains any non-digits
		if(bool(re.search(r'\D', input_string))):
			raise IDError("Input contains non-numbers")
		else:
			leagueId = int(input_string)
			return leagueId

	raise IDError("No League ID could be found")
