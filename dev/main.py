from .core import scrape
from .prodict import Prodict
import os, time, json, datetime, googlemaps, sys, importlib, colorama
from .core import data as D
from geopy.geocoders import Nominatim
from colorama.ansi import Fore
from bson import json_util
from . import utils
import geopy

class Data(Prodict):
	agencies:			list[str] #agency names
	last_scanned:		int
	last_incidents:		list
	analyzed:			list
	def init(self):
		self.agencies = []
		self.last_incidents = []
		self.analyzed = []
		self.last_scanned = 0


class Main:
	def __init__(self, config_file="config.json", keys_file="keys.json"):
		from . import events
		self.config_file = config_file
		self.keys_file = keys_file
		colorama.init()
		self.GEOCODE_LIMIT = 50
		self.api_calls = 0 #maybe some day i'll throw in some code that makes this reset every day.
		self.incident_type_tags = utils.load_json("typetags.json") or {}
		self.config:D.Cfg = None
		self.keys = None
		with open(keys_file, "r") as f:
			self.keys = json.loads(f.read())
		
		self.checks:list[function] = []
		self.events:list[events.Events] = []
		self.data = Data()
		self.scraper = scrape.Scraper()
		self.load_config(self.config_file)
		self.loop_control()

	def loop_control(self):
		DEVMODE = True
		print(self.config.locations)
		while True:
			if DEVMODE:
				self.main_loop() #show any errors and crash
			else:
				try:
					self.main_loop()
				except Exception as e:
					print(e)
			
			time.sleep(self.config.scan_interval)


	def main_loop(self):
		self.call_event("main_loop_start") #! EVENT !#
		
		self.data.last_scanned = time.time() 
		incidents:list[D.Incident] = [] #incidents to analyze
		
		for a in self.data.agencies:
			i = self.scraper.get_incidents(a)
			if i.active == None: i.active = []
			if i.recent == None: i.recent = []
			incidents1 = i.active + i.recent#basically just all of the incidents for this agency, both active and recent
			for x in incidents1:
				if x.uid not in self.data.analyzed:
					self.call_event("incident_found", x) #! EVENT !#
					incidents.append(x)
		
		for x in self.call_event("get_custom_incidents"): #! EVENT !#
			if x.uid not in self.data.analyzed:
				self.call_event("incident_found", x) #! EVENT !#
				incidents.append(x)
		
		self.call_event("analysis_start") #! EVENT !#
		for x in incidents:
			self.analyze(x)
			self.data.analyzed.append(x.uid)
			self.call_event("incident_analyzed", x) #! EVENT #!
		self.call_event("main_loop_end") #! EVENT #!
		utils.save_json("geocoding_results.json", self.geocoding_results)
		current_type_tags = utils.load_json("typetags.json") or {}
		self.incident_type_tags.update(current_type_tags) #if we've changed anything while the program was running, be sure to not discard those changes
		utils.save_json("typetags.json", self.incident_type_tags)

	
	def analyze(self, incident:D.Incident):
		if incident.incident_type != None and incident.incident_type not in self.incident_type_tags:
			self.incident_type_tags[incident.incident_type] = []
		incident.significant_locations = []
		if self.config.incident_filters.allowed(incident.incident_type) == False: return #if this incident is blocked or not allowed (global), skip analysis

		for x in self.config.locations:
			if x.filters.allowed(incident.incident_type) == False: continue #if this incident is blocked or not allowed (per location), skip analysis for this location.
			checktotal = 0
			for c in self.checks:
				checktotal += c(self, incident, x)
			if checktotal > 0: incident.significant_locations.append(x.name)
		
		if len(incident.significant_locations) == 0:
			return
		# one or more significant locations. Find the most important one
		importantLocation = self.get_location(incident.significant_locations[0])
		for x in incident.significant_locations:
			l = self.get_location(x)
			if l.importance > importantLocation.importance: importantLocation = l
		self.call_event("important_incident_found", incident, importantLocation, importantLocation.importance)
	

	def get_location(self, name):
		for x in self.config.locations:
			if x.name == name: return x
		return None


	def call_event(self, event_name, *args):
		ret = None
		for x in self.events:
			r = x.__getattribute__(event_name)(*args)
			if r != None:
				ret = r
		return ret
		

	def load_event_script(self, scriptname):
		script = importlib.import_module(f".", f"dev.event_modules.{scriptname}").Events
		module_instance = script()
		module_instance.main = self
		self.events.append(module_instance)
		module_instance.__getattribute__("post_init")()
		return module_instance
	
	def load_check_script(self, scriptname):
		funct = importlib.import_module(f".", f"dev.importance.{scriptname}").check
		self.checks.append(funct)
		return funct
	
	def print(self, *args, t="normal", end=None):
		"""Prints stuff. "normal", "good", "warn", "bad", 
		"""
		colors = {"normal": Fore.BLUE,  "good":Fore.GREEN, "warn": Fore.YELLOW, "bad": Fore.RED, "important": Fore.MAGENTA}
		if t not in colors: t == "warn"
		p = f"{colors[t]}{colorama.Style.BRIGHT}"
		sys.stdout.write("\033[K") #clear line
		print(p, *args, colorama.Style.RESET_ALL)
		#if end == '\r':
		#	sys.stdout.write("\033[F") #back to previous line 

	def load_config(self, config_file):
		#removed json4json because that library (the one that i made) kinda sucks.
		self.config = D.Cfg.from_dict(utils.load_json(config_file))
		self.init_maps()
		
		for a_id in self.config.agencies:
			self.data.agencies.append(a_id) #add agencies to the list of agencies we run through every scan.
		
		for x in self.config.events:
			self.load_event_script(x)
		for x in self.config.importance_checks:
			self.load_check_script(x)
		
		self.print("Configuration loaded.", t='good')
		

	def init_maps(self):
		self.geocoding_results = utils.load_json("geocoding_results.json") or {} #if loading json results in None, just use a new dictionary

		self.nominatim = Nominatim(user_agent="Pulsepoint Scraper", timeout=self.config.geocoder_timeout) #use this before attempting to use google maps

		if "gmaps" not in self.keys or self.keys["gmaps"] == "":
			self.gmaps = None
			self.print("google maps failed to load. Geocoding will be more prone to failiure.", t="warn")
			return
		else:
			try: self.gmaps = googlemaps.Client(key=self.keys['gmaps']) #works better than nominatim but is more expensive
			except: self.print("Could not load google maps. Probably an invallid api key.", t='bad')


	def validate_location(self, l:D.CfgLocation):
		if l.coords != None: return True
		if l.address != None and l.coords == None:
			try:
				l.coords = self.get_coords(l.address)
				return True
			except Exception as e:
				return False
	
	def get_coords(self, address) -> tuple[float, float]:
		if address.upper() in self.geocoding_results:
			self.print(f"Api calls were saved because the address {address} was previously geocoded!", t='good')
			return self.geocoding_results[address.upper()]
		
		coords = None
		location = None
		#first try using nominatim
		try: location = self.nominatim.geocode(address)
		except: pass
		if location == None:
			#nominatim doesn't work, so try using google maps
			if self.gmaps != None:
				self.api_calls += 1
				if self.api_calls < self.GEOCODE_LIMIT:
					failed = False
					try:
						#! MAKING GOOGLE MAPS API CALLS. TOO MANY OF THESE CAN COST REAL MONEY !#
						#! ONLY ENABLE GMAPS IF YOU'RE AWARE OF THE RISKS AND KNOW WHAT YOU'RE DOING #!
						self.print(f"MAKING AN API CALL! {self.GEOCODE_LIMIT - self.api_calls} CALL(S) LEFT!", t='warn')
						l = self.gmaps.geocode(address)[0]['geometry']['location']
						coords = (float(l["lat"]), float(l["lng"])) #google maps worked after nominatim failed, define the coordinates
						self.print("API CALL MADE!", coords, t='good')
					except:
						failed = True
					if failed:
						#sometimes there'll be a random "[...." in the address, removing this might fix things
						if "[" in address:
							self.print(f"API CALL FAILED FOR ADDRESS {address}! TRYING AGAIN...", t='warn')
							coords = self.get_coords(address.split("[")[0])
							if coords == [0, 0]:
								self.print("API CALL FAILED!", t='bad')
								coords = None
							else:
								self.print("SUCCESSFULLY GEOCODED WEIRD LOOKING ADDRESS!", t='good')
						else:
							self.print(f"API CALL FAILED FOR ADDRESS {address}!", t="bad")
				else:
					self.print("GEOCODE CALL LIMIT REACHED! Error getting coordinates for {address}!", t='bad')
			else: #neither of these work.
				self.print(f"error getting coordinates for {address}!", t='warn')
		else: #nominatim worked, define the coordinates
			coords = (location.latitude, location.longitude)
		if coords != None:
			self.geocoding_results[address.upper()] = coords
		
		time.sleep(.4) #rate limiting
		return coords 
