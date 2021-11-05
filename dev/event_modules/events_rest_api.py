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
		self.flaskapp = rest_api.FlaskAPI(self)
		self.recents = [] #list of events, max size = 100
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


	#called the moment a new incident is found. this is before any analysis is done, so there won't be a 'coords' property in it
	def incident_found(self, incident:D.Incident):
		a = {
			"date": incident.CallReceivedDateTime.strftime("%M/%d"),
			"time": incident.CallReceivedDateTime.strftime("%H:%m"),
			"epoch": incident.CallReceivedDateTime.timestamp(),
			"agency": incident.agency_name,
			"type": incident.incident_type,
			"address": incident.FullDisplayAddress,
			"coords": incident.coords
		}
		self.recents.append(a)
		self.data.incident_frequency_table[0].append(incident.CallReceivedDateTime)
		self.data.incident_frequency_table[1].append(1)
		self.main.print(f"{incident.incident_type} found at {incident.FullDisplayAddress}.", incident.coords, end='\r')
		pass
	
	#called when an agency is put into the queue.
	def agency_queue_enter(self, agency:str):
		self.main.print(f"Added agency {agency} to the queue.", t='good', end='\r')
		pass
	
	def analysis_start(self):
		pass
	
	def important_incident_found(self, incident:D.Incident, location:D.CfgLocation, importance:int):
		return


#custom helper method
def GetLocationByName(main, name):
	for x in main.config['locations']:
		if x['name'] == name:
			return x
	main.print(f'could not find location using name "{name}"', t='bad')
