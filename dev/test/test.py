#this is to test how long incidents remain visible on an agency. is every 12 hours really enough? or should we be scanning more frequently?

import pymongo
from ..ppdb import ppdb
from .. import utils
from ..main import scrape
import datetime, time, sys
class Main:
	def __init__(self):
		self.config = ppdb.Config.from_dict(utils.load_json("dbconfig.json"))
		self.client = pymongo.MongoClient(self.config.mongodb_client)
		self.target = 79
		self.scraper = scrape.Scraper()
		self.db = self.client["pulsepoint"]
		self.coll = self.db["test"]
		if "analyze" in "".join(sys.argv):
			self.analyze()
			return


		while True:
			self.main_loop()
			print("scraped!")
			time.sleep(60*15)
	
	def analyze(self):
		incidents_analyzed = []
		observations = []
		#go through until we find a NEW incident
		data = list(self.coll.find({}))
		
		def get_new():
			last_ones = data[0]["incidents"]
			for d in data:
				for i in d["incidents"]:
					if i not in last_ones and i not in incidents_analyzed:
						return i
		
		while True:
			incident = get_new()
			print(incident)
			if incident == None:
				break
			#find how long the incident lasts for
			start = None
			end = None
			for i, d in enumerate(data):
				if start == None and incident in d["incidents"]:
					start = d["timestamp"]
				elif start != None and incident not in d["incidents"]:
					end = data[i - 1]["timestamp"]
					break
			if end != None:
				observations.append({"id": incident, "start": start, "end": end, "length (hours)": round((end - start).total_seconds() / 60 / 60, 3)})
			incidents_analyzed.append(incident)
		print("Done!")
		for x in observations:
			print(x["id"], "\t\t", x["length (hours)"], x["start"].isoformat(), x["end"].isoformat())





	def main_loop(self):
		a = self.db["agencies"].find_one({"_id": self.target})
		incidents = self.scraper._agency_raw_data(a["agencyid"])["incidents"]
		if incidents["active"] == None: incidents["active"] = []
		if incidents["recent"] == None: incidents["recent"] = []

		allincidents = incidents["recent"] + incidents["active"]
		incident_ids = [x["ID"] for x in allincidents]
		item = {"timestamp": datetime.datetime.now(), "incidents": incident_ids}
		self.coll.insert_one(item)
		


