from .. import events, utils
from ..core import data as D
from notifiers import get_notifier
from geopy.distance import geodesic

from bs4 import BeautifulSoup
import requests, datetime
from .. import utils



class Events(events.Events):
	def __init__(self):
		print("HIIIIIi")
		self.analyzed = []
		self.previouslyCollected = []

	def get_custom_incidents(self) -> list[D.Incident]:			
		soup = BeautifulSoup(requests.get("https://www.pdxpolicelog.com").text, features="html.parser")
		unparsed = soup.find_all("div", {"class": "rt-BaseCard"})

		incidents = []
		for x in unparsed:
			#each of these has incident data
			x1 = x.find("div")
			title = x1.find('h2').text.split("at")
			incident_type = title[0].strip()
			locationDesc = title[1].strip()
			t = x1.find("span").text.split(" ") #time May 18, 2025, 10:31:30 AM
			months = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
			month = months[t[0]]
			day = int(t[1].split(",")[0])
			year = int(t[2].split(",")[0])
			tt = t[3].split(":")
			h = int(tt[0])
			if t[4] == "PM": h += 12
			if h == 24: h = 0
			m = int(tt[1])
			date = datetime.datetime(year, month, day, h, m)
			#date = utils.local_to_utc(date).replace(tzinfo=None) #convert to UTC
			coordsUnparsed = x1.find("a").get("href").split("query=")[1].split(",")
			coords = [float(coordsUnparsed[0].strip()), float(coordsUnparsed[1].strip())]

			i = D.Incident()
			i.incident_type = incident_type
			i.CallReceivedDateTime = date
			i.Latitude = coords[0]
			i.Longitude = coords[1]
			i.coords = coords
			i.FullDisplayAddress = locationDesc
			i.uid = hash(i.incident_type + i.CallReceivedDateTime.strftime("MM/DD/YYYY:hh:mm") + str(coords))
			if i.uid not in self.previouslyCollected:
				self.previouslyCollected.append(i.uid)
				incidents.append(i)
		
		return incidents


	#called the moment a new incident is found. this is before any analysis is done, so there won't be a 'coords' property in it
	def incident_found(self, incident:D.Incident):
		self.main.print(f"{incident.incident_type} found at {incident.FullDisplayAddress}.", incident.coords, end='\r')
		pass
	#called when an agency is put into the queue.
	def agency_queue_enter(self, agency:str):
		self.main.print(f"Added agency {agency} to the queue.", t='good', end='\r')
		pass
	def analysis_start(self):
		pass
	def analysis_end(self):
		pass
	
	def important_incident_found(self, incident:D.Incident, location:D.CfgLocation, importance:int):
		p = get_notifier("pushover")
		address = ""
		if location.address != None: address = location.address
		distance = "N/A"
		if incident.dists != None and location.name in incident.dists: distance = incident.dists[location.name]
		message = f"""{incident.incident_type.upper()} AT {location.name.upper()}
	Time:				{utils.local(incident.CallReceivedDateTime).strftime("%a, AT %H:%M")}
	Incident Address:		{incident.FullDisplayAddress.upper()}
	Monitored address:		{address.upper()}
	Incident coords:		{incident.coords}
	Distance:			{"%03d" % distance} meters""".upper()

		self.main.print(message, t='important')
		p.notify(user=self.main.keys["pushover_user"], token=self.main.keys["pushover_token"], message=message)
		pass


#custom helper method
def GetLocationByName(main, name):
	for x in main.config['locations']:
		if x['name'] == name:
			return x
	main.print(f'could not find location using name "{name}"', t='bad')
