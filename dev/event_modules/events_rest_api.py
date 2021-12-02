import flask, os, json
from .. import events
from ..core import data as D
from notifiers import get_notifier
from geopy.distance import geodesic
from ..prodict import Prodict
from bson import json_util
import time, datetime
import pandas as pd
from .. import utils
import haversine as hs
from .flask import rest_api

class SaveData(Prodict):
	incidents:	list[D.Incident]
	agency_filters:	dict[str, list[str]]
	incident_frequency_table: tuple[list[datetime.datetime], list[int]]

	def init(self):
		self.incidents = []
		self.agency_filters = {}
		self.incident_frequency_table = ([], [])




class Events(events.Events):
	def __init__(self):
		pass
	
	def post_init(self):
		self.flaskapp = rest_api.FlaskAPI(self)
		self.recents = [] #list of events, max size = 500
		self.important_incidents = [] #list of [incident, location], max size = 100
		self.data:SaveData = None
		self.load_data()
		self.agency_data = utils.load_json("allagencydata.json")
		super().__init__()
	
	def save_config(self):
		utils.save_json(self.main.config_file, self.main.config)

	def load_data(self):
		if os.path.exists("dev/event_modules/flask/data.json") == False:
			with open('dev/event_modules/flask/data.json', "w+") as f: f.write("{}")
		with open("dev/event_modules/flask/data.json", "r") as f:
			self.data:SaveData = SaveData.from_dict(json.loads(f.read(), object_hook=json_util.object_hook))
	
	def save_data(self):
		with open("dev/event_modules/flask/data.json", "w+") as f:
			f.write(json.dumps(self.data.to_dict(is_recursive=True), default=json_util.default, indent=4))

	def utc2local(self, utc) -> datetime.datetime:
		epoch = time.mktime(utc.timetuple())
		offset = datetime.datetime.fromtimestamp(epoch) - datetime.datetime.utcfromtimestamp(epoch)
		return utc + offset

	def simplify_incident(self, incident:D.Incident):
		a = {
			"datelocal": utils.local(incident.CallReceivedDateTime).strftime("%m/%d"),
			"daylocal": utils.local(incident.CallReceivedDateTime).strftime("%a"),
			"timelocal": utils.local(incident.CallReceivedDateTime).strftime("%H:%M"),
			"epochlocal": utils.local(incident.CallReceivedDateTime).timestamp(),
			"date": incident.CallReceivedDateTime.strftime("%m/%d"),
			"day": incident.CallReceivedDateTime.strftime("%a"),
			"time": incident.CallReceivedDateTime.strftime("%H:%M"),
			"epoch": incident.CallReceivedDateTime.replace(tzinfo=None).timestamp(),
			"agency": incident.agency_name,
			"type": incident.incident_type,
			"address": incident.FullDisplayAddress,
			"coords": incident.coords
		}
		return a
	#called the moment a new incident is found. this is before any analysis is done, so there won't be a 'coords' property in it
	def incident_found(self, incident:D.Incident):
		a = self.simplify_incident(incident)
		if self.incident_in_range(incident) == False: return
		self.recents.append(a)
		self.recents.sort(key= lambda x : x['epoch'], reverse=True)
		self.recents = self.recents[:1000]
		self.data.incident_frequency_table[0].append(incident.CallReceivedDateTime)
		self.data.incident_frequency_table[1].append(1)
		#self.main.print(f"[{utils.local(incident.CallReceivedDateTime)}] {incident.incident_type} found at {incident.FullDisplayAddress}.", incident.coords, end='\r')
		#time.sleep(.15)
		pass
	
	#called when an agency is put into the queue.
	def agency_queue_enter(self, agency:str):
		self.main.print(f"Added agency {agency} to the queue.", t='good', end='\r')
		pass
	
	def analysis_start(self):
		pass
	def main_loop_end(self):
		self.flaskapp.save_logs()
	def important_incident_found(self, incident:D.Incident, location:D.CfgLocation, importance:int):
		a = self.simplify_incident(incident)
		distance = "N/A"
		if incident.dists != None and location.name in incident.dists: distance = incident.dists[location.name]
		a["location_name"] = location.name
		a["distance"] = distance
		a["monitored_address"] = location.address
		self.important_incidents.append(a)
	
	def incident_in_range(self, incident:D.Incident) -> bool:
		closest = 0
		closestDist = 1000000
		for l in self.main.config.locations:
			if l.coords != None and incident.coords != None:
				dist = hs.haversine(l.coords, incident.coords, unit=hs.Unit.METERS)
				if dist < closestDist:
					closestDist = dist
					if closestDist < self.main.config.map_config.minimum_distance: #at some point i should change that to "maximum distance" because that's what it really is.
						return True
		return False
		
		


#custom helper method
def GetLocationByName(main, name):
	for x in main.config['locations']:
		if x['name'] == name:
			return x
	main.print(f'could not find location using name "{name}"', t='bad')
