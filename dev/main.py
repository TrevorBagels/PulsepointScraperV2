from .core import scrape
from .prodict import Prodict
from JSON4JSON import JSON4JSON
import os, time, json, datetime, googlemaps, sys, importlib, colorama
from .core import data as D
from geopy.geocoders import Nominatim
from colorama.ansi import Fore

class AgencyData(Prodict):
	name:				str
	frequency:			int
	last_scanned:		int
	ID:					str

class Data(Prodict):
	agencies:			list[AgencyData]
	queue:				list[str] # agency names
	last_incidents:		list
	analyzed:			list
	def init(self):
		self.agencies = []
		self.queue = []
		self.last_incidents = []
		self.analyzed = []

class CfgAgency(Prodict):
	name:				str
	scan_interval:		int #seconds, overrides scan_interval

class CfgLocation(Prodict):
	name:				str
	address:			str
	coords:				tuple[float, float]
	radius:				float #in meters
	importance:			int
	match:				str #regex expression
	filters:			D.Filter
	def init(self):
		self.filters = D.Filter()

class Cfg(Prodict):
	importance_checks:	list[str]
	events:				list[str]
	api_key:			str #google maps API key
	pushover_token:		str #pushover token
	pushover_user:		str #pushover USER token
	scan_interval:		int #seconds, how long to wait in between scans
	agencies:			list[CfgAgency]
	locations:			list[CfgLocation]


class Main:
	def __init__(self, config_file="config.json"):
		from . import events
		colorama.init()
		self.GEOCODE_LIMIT = 50
		self.api_calls = 0
		self.config = None
		self.checks:list[function] = []
		self.events:list[events.Events] = []
		self.data = Data()
		self.scraper = scrape.Scraper()
		self.load_config(config_file)
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
			
			time.sleep(5)


	def main_loop(self):
		self.call_event("main_loop_start") #! EVENT !#
		# reset the queue
		self.data.queue = []
		for a in self.data.agencies:
			if a.last_scanned < time.time() - a.frequency:
				self.data.queue.append(a.ID)
				self.call_event("agency_queue_enter", a.name) #! EVENT !#
				a.last_scanned = time.time()
		if len(self.data.queue) == 0: return # return if the queue is empty (nothing to do)
		
		incidents:list[D.Incident] = [] #incidents to analyze

		for a in self.data.queue:
			i = self.scraper.get_incidents(a)
			if i.active == None: i.active = []
			if i.recent == None: i.recent = []
			incidents1 = i.active + i.recent
			for x in incidents1:
				if x.uid not in self.data.analyzed:
					self.call_event("incident_found", x) #! EVENT !#
					incidents.append(x)

		self.call_event("analysis_start") #! EVENT !#
		for x in incidents:
			self.analyze(x)
			self.data.analyzed.append(x.uid)

	
	def analyze(self, incident:D.Incident):
		incident.significant_locations = []
		for x in self.config.locations:
			checktotal = 0
			for c in self.checks:
				checktotal += c(self, incident, x)
			
			if checktotal > 0: incident.significant_locations.append(x.name)

		if len(incident.significant_locations) == 0: return
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
		#ret = None
		for x in self.events:
			x.__getattribute__(event_name)(*args)
		#return ret
		

	def load_event_script(self, scriptname):
		script = importlib.import_module(f".", f"dev.event_modules.{scriptname}").Events
		module_instance = script()
		module_instance.main = self
		self.events.append(module_instance)
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
		j4j = JSON4JSON()
		j4j.load(config_file, "./dev/rules.json")
		self.config = Cfg.from_dict(j4j.data)
		self.init_maps()
		for x in self.config.agencies:
			a_id = self.scraper.get_agency(x.name)['agencyid']
			self.data.agencies.append(AgencyData(name=x.name, frequency=x.scan_interval, last_scanned=0, ID=a_id))
		for x in self.config.locations:
			if self.validate_location(x) == False:
				self.print(f"Could not geocode address for \"{x.name}\"", t='warn')
		
		for x in self.config.events:
			self.load_event_script(x)
		for x in self.config.importance_checks:
			self.load_check_script(x)
		
		self.print("Configuration loaded.", t='good')
		

	def init_maps(self):
		if self.config.api_key == "":
			self.gmaps = Nominatim(user_agent="Pulsepoint Scraper")
			return
		try:
			self.gmaps = googlemaps.Client(key=self.config.api_key)
		except:
			self.print("Could not load google maps. Probably an invallid api key.", t='bad')


	def validate_location(self, l:CfgLocation):
		if l.coords != None: return True
		if l.address != None and l.coords == None:
			try:
				l.coords = self.get_coords(l.address)
				return True
			except Exception as e:
				return False
	
	def get_coords(self, address) -> tuple[float, float]:
		if self.api_calls >= self.GEOCODE_LIMIT:
			print("GEOCODE CALL LIMIT REACHED!!!", t='warn')
			return (0, 0)
		self.api_calls += 1
		if self.config.api_key == "":
			location = self.gmaps.geocode(address)
			time.sleep(.5) #rate limiting
			return (location.latitude, location.longitude)
		else:
			#! MAKES API CALLS. I AM NOT RESPONSIBLE FOR ANY DAMAGES CAUSED BY THIS. Set api_key to "" to avoid using google maps.
			l = self.gmaps.geocode(address)[0]['geometry']['location'] 
			return (float(l["lat"]), float(l["lng"]))