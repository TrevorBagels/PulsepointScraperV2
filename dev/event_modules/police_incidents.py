
from typing import NewType
from .. import events
from ..core import data as D
from notifiers import get_notifier
from geopy.distance import geodesic
import os, requests, datetime
from .. import utils


class Events(events.Events):
	def __init__(self):
		self.data:list[D.Incident] = []
		self.analyzed = []
		self.accounts = ["1365077991252914179"]
		self.most_recent:dict[str, int] = {}
		for x in self.accounts:
			self.most_recent[x] = None
		pass
	def post_init(self):
		self.headers = {"Authorization": f"Bearer {self.main.keys['twitterbearertoken']}"}
		self.url = ""
	#called the moment a new incident is found. this is before any analysis is done, so there won't be a 'coords' property in it
	def get_custom_incidents(self) -> list[D.Incident]:
		MAX_RESULTS = 100#50 #set this to 10 when testing
		print("Getting custom incidents...")
		incidents = []
		for user in self.accounts:
			new_tweet_count = None
			if self.most_recent[user] != None:
				print("Most Recent:", self.most_recent[user])
				new_tweet_count = requests.get(f"https://api.twitter.com/2/tweets/counts/recent?query=from:{user}&since_id={self.most_recent[user]}", headers=self.headers).json()['meta']['total_tweet_count']
			if self.most_recent[user] == None or new_tweet_count > 0:
				if new_tweet_count != None: self.main.print(f"{new_tweet_count} tweet(s) found for user {user}.", t='good')
				tweets_request_url = f"https://api.twitter.com/2/users/{user}/tweets?tweet.fields=created_at&max_results={MAX_RESULTS}"
				if self.most_recent[user] != None:
					tweets_request_url += f"&since_id={self.most_recent[user]}"
				tweets = requests.get(tweets_request_url, headers=self.headers).json()
				if "data" not in tweets:
					self.main.print(tweets, t='bad')
				try:
					print(len(tweets['data']), "tweets recieved")
				except:
					print("UH OH ", tweets)
				for x in tweets['data']:
					x['id'] = int(x['id'])
					
					if self.most_recent[user] == None or x['id'] > self.most_recent[user]: #assigning the most recent tweets from this user
						self.most_recent[user] = x['id']
					
					if x["id"] in self.analyzed: continue
					self.analyzed.append(x["id"])
					i = self.get_incident_from_tweet(x)
					if i == None: continue
					incidents.append(i)
					self.data.append(i)
				self.save_data()
				return incidents
	
	def get_incident_from_tweet(self, x, dept="Police") -> D.Incident:
		#dept could also be "Fire", for parsing incidents from @pdxfirelog. pdx fire log includes more data (like when police are requested, or when someone is jumping from a bridge, etc.)
		i = D.Incident()
		txt = x['text']
		cities = {"PORT": "Portland", "GRSM": "Gresham", "BEAV": "Portland", "WASH": "Portland", "MULT": "Portland"} #, PORT [Portland Police #... or GRSM [Gresham Police #...
		city = None #either "PORT" or "GRSM"
		for c in cities:
			if f"{c} [{cities[c]} {dept} #" in txt:
				city = c
		if city == None:
			self.main.print(txt, t='bad')
			return None
		
		i.incident_type = txt.split(" at ")[0] #! incident type assigned
		addy = txt.split(i.incident_type + " at ")[1].split(f", {city} [")[0] #<- .split(", PORT [") or .split(", GRSM, [")
		i.FullDisplayAddress = addy.replace(" / ", " & ") + f", {cities[city]} OR" #!incident address assigned

		time = txt.split(addy + f", {city} [")[1].split("]")[1].split("#")[0].strip() #gets the time 00:00 of the incident provided in the tweet text
		#finding the date and time of the incident (LOCAL TIME)
		hour = int(time.split(":")[0])
		minute = int(time.split(":")[1])
		#date can be found because we know the time was BEFORE the current time
		dp = utils.local(datetime.datetime.strptime(x['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ")) #date posted (IN PDT/LOCAL, NOT UTC)
		#if the time is say... 21:00, and the day the thing was posted was one day later at 00:00, then we know that it was one day before...
		date = datetime.datetime(dp.year, dp.month, dp.day, hour, minute)
		#so if the hour of day posted is LESS than the hour of the incident time, then the incident took place 1 day earlier. otherwise, the date is accurate.
		if dp.hour < hour: #date posted is one day ahead than the actual incident, subtract a day
			date = date - datetime.timedelta(days=1)
		#date = local time in which the incident occured.
		#we should convert the date back to UTC because all the other incidents use UTC for their timestamps
		date = utils.local_to_utc(date).replace(tzinfo=None) #because the other pulsepoint incidents don't have TZINFO.
		i.CallReceivedDateTime = date #! incident date received assigned
		#we'll assume the time it was closed is the same as the time the thing was posted 
		i.ClosedDateTime = datetime.datetime.strptime(x['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ") #! incident date closed assigned
		i.uid = str(x["id"]) #! incident UID assigned
		#? what about coords?
		coords = self.main.get_coords(addy)
		if coords == None:
			self.main.print("ERROR: Could not find coords for incident #" + i.uid)
			i.coords = [0, 0]
		else:
			i.coords = coords #! incident coords assigned
			i.Latitude = coords[0] #! incident latitude assigned
			i.Longitude = coords[1] #! incident longitude assigned
		if i.coords == None: print(i)
		return i

	def save_data(self):
		utils.save_json("./dev/event_modules/police_incidents.json", self.data)
	def load_data(self):
		self.data = utils.load_json("./dev/event_modules/police_incidents.json")

#custom helper method
def GetLocationByName(main, name):
	for x in main.config['locations']:
		if x['name'] == name:
			return x
	main.print(f'could not find location using name "{name}"', t='bad')
