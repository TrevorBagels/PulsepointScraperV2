import pymongo
from ..prodict import Prodict
from .. import utils
from ..core import scrape
from time import sleep
import requests, datetime, json, sys
class Config(Prodict):
	mongodb_client:		str
	dbname:				str
	check_interval:		int #seconds
	margin:				int #seconds

	def init(self):
		self.mongodb_client = "mongodb://localhost:27017/"
		self.dbname = "pulsepoint"
		self.check_interval = 12 * 60 * 60 #every 12 hours
		self.margin = 60*45 # 45 minute check margin

def to_time(seconds):
	seconds = int(seconds)
	hours = int(seconds / 3600)
	mins = int((seconds%3600)/60)
	sec = int((seconds%3600)%60)
	return datetime.datetime(year=2021, month=1, day=1, hour=hours,minute=mins,second=sec)


class PPDB:
	def __init__(self):
		self.config = Config.from_dict(utils.load_json("dbconfig.json"))
		self.client = pymongo.MongoClient(self.config.mongodb_client)
		self.setup_database()
		self.scraper = scrape.Scraper()
		if self.db["agencies"].find_one() == None:
			self.scan_agency_info()
		while True:
			self.main_loop()
			sleep(30)
			
	
	def get_time_query(self):
		q = {}
		before = datetime.datetime.now() - datetime.timedelta(seconds=60*60*11)
		after = datetime.datetime.now() - datetime.timedelta(seconds=60*60*11)
		q = {"$not": {"$gt": before, "$lt": after}}
		return q

	def log_incidents(self, a_id):
		a = self.db["agencies"].find_one({"_id": a_id})
		failed = False
		print("Getting incidents from ", a["agencyname"])
		try:
			incidents = self.scraper._agency_raw_data(a["agencyid"])["incidents"]
		except:
			failed = True
			print("Something went wrong, taking a short break...")
		if failed == False:
			if incidents["active"] == None: incidents["active"] = []
			if incidents["recent"] == None: incidents["recent"] = []
			for i in incidents["active"] + incidents["recent"]:
				i['_id'] = i["AgencyID"] + "-" + i['ID']
				for k, v in i.items():
					if v == "null": i[k] == None
				
				to_datetime = ["CallReceivedDateTime", "ClosedDateTime"]
				toint = ["PublicLocation", "IsShareable"]
				tofloat = ["Latitude", "Longitude"]
				remove = []
				if "PulsePointIncidentCallType" in i:
					i["Type"] = self.scraper.incident_types[i["PulsePointIncidentCallType"]]
				if "Latitude" in i:
					i['coordinates'] = {"type": "Point", "coordinates": [float(i['Longitude']), float(i['Latitude'])] }
				for k in to_datetime:
					if k in i and i[k] != "null":
						i[k] = utils.from_iso8601(i[k])
				for k in toint:
					if k in i and i[k] != "null":
						i[k] = int(i[k])
				for k in tofloat:
					if k in i and i[k] != "null":
						i[k] = float(i[k])
				for k in remove:
					if k in i:
						del i[k]
				if "Unit" in i:
					for u in i["Unit"]:
						if "UnitClearedDateTime" in u:
							u["UnitClearedDateTime"] = utils.from_iso8601(u["UnitClearedDateTime"])
				
				self.db["incidents"].update({"_id": i["_id"]}, i, upsert=True)
			self.db["schedule"].find_and_modify({"_id": a_id}, {"$set": {"last_update": datetime.datetime.now()}})
		else:
			sleep(10)




	def main_loop(self):
		for a in self.db['schedule'].find({"last_update": self.get_time_query()}):
			if self.should_update(a):
				self.log_incidents(a["_id"])
			


	def setup_database(self):
		self.db = self.client[self.config.dbname]
		collections = ["agencies", "incidents", "schedule"]
		for collection_name in collections:
			if collection_name not in self.db.list_collection_names():
				self.db.create_collection(collection_name)
	
	def scan_agency_info(self):
		agenciesjson = requests.get("https://web.pulsepoint.org/DB/GeolocationAgency.php").json()["agencies"]
		index = 0
		per_agency_interval = (12*60*60) / len(agenciesjson)
		for a in agenciesjson:
			
			a["_id"] = int(a["id"])
			a["coordinates"] = {"type": "Point", "coordinates": [float(a["agency_longitude"]), float(a["agency_latitude"])]}
			a["agency_latitude"] = float(a["agency_latitude"])
			a["agency_longitude"] = float(a["agency_longitude"])
			geofence = {"type": "Polygon", "coordinates": [[]]}
			if 'boundary' in a:
				for value in a["boundary"].replace("POLYGON((", "").replace("))", "").split(","):
					xy = value.split(" ")
					geofence["coordinates"][0].append([float(xy[0]), float(xy[1])])
				a["boundary"] = geofence
			self.db["agencies"].update_one({"_id": a["_id"]}, {"$set": a}, upsert=True)

			time_1 = to_time(per_agency_interval * index)
			time_2 = to_time(per_agency_interval * index + (12*60*60))

			schedule = {"_id": a["_id"], "name": a["agencyname"], "times": [time_1, time_2], "last_update": datetime.datetime(year=1990, month=1, day=1)}
			self.db["schedule"].update_one({"_id": schedule["_id"]}, {"$set": schedule}, upsert=True)
			index += 1
	
	def should_update(self, a):
		#a = self.db['schedule'].find({"_id": _id})
		now = datetime.datetime.now().time()
		do_update = False
		if (datetime.datetime.now() - a["last_update"]).total_seconds() < self.config.margin * 2:
			return False
		for _t in a['times']:
			t = datetime.datetime.combine(datetime.date.min, datetime.time(hour=_t.hour, minute=_t.minute, second=_t.second))
			if abs(( datetime.datetime.combine(datetime.date.min, now) - t).total_seconds()) <= self.config.margin:
				do_update = True
		
		return do_update