from calendar import month
from typing import Union
from ..prodict import Prodict
from datetime import datetime


class AgencyData(Prodict):
	name:				str
	frequency:			int
	last_scanned:		int
	ID:					str

class Filter(Prodict):
	allow_list:		list[str] #if empty, will allow all, unless block list = *. then things in this list override block list
	block_list:		list[str]

	def init(self):
		self.allow_list = []
		self.block_list = []
	
	def allow_item(self, item):
		if item in self.allow_list: return
		if item in self.block_list:
			self.block_list.remove(item)
			if "*" in self.block_list: #allow the item if we're already blocking everything
				self.allow_list.append(item)
			return
		if "*" not in self.block_list:
			self.block_list.append("*")
		self.allow_list.append(item)
	def block_item(self, item):
		if item in self.allow_list: self.allow_list.remove(item)
		if item not in self.block_list:
			self.block_list.append(item)
	
	def get_allowed(self) -> str:
		if len(self.allow_list) == 0 and "*" not in self.block_list:
			return "all"
		else:
			if len(self.allow_list) > 0:
				return ", ".join(self.allow_list)
			else: return "none"
	def get_blocked(self) -> str:
		if "*" in self.block_list:
			return "all"
		else:
			if len(self.block_list) > 0:
				return ", ".join(self.block_list)
			else: return "none"

	def allowed(self, item):
		if item in self.block_list:
			return False
		if item in self.allow_list:
			return True
		if "*" in self.block_list:
			if item not in self.allow_list:
				return False
		else: #we aren't blocking anything, do we have filters set up yet?
			if len(self.allow_list) <= 0:
				return True








class CfgLocation(Prodict):
	name:				str
	address:			str
	coords:				tuple[float, float]
	radius:				float #in meters
	importance:			int
	match:				str #regex string
	filters:			Filter
	enabled:			bool #can be turned to false to disable monitoring this location
	def init(self):
		self.name = ""
		self.address = ""
		self.radius = 50
		self.importance = 1
		self.match = None
		self.filters = Filter()
		self.enabled = True 
class MapCfg(Prodict):
	max_cluster_radius:	int
	tiles:				str
	zoom_start:			int
	active_hours:		int #how long ago until this incident on the map turns gray and is considered inactive?
	max_hours:			int #how long until the incident is no longer displayed on the map?
	minimum_distance:	int #how close does the incident need to be to a relevant location in order to be displayed on the map?
	minimum_line_distance:	int #how close does the incident need to be to a relevant location in order to have lines drawn on it?
	line_opacity:			float
	thermal_min_opacity:	float
	thermal_max_zoom:		float
	thermal_blur:			float
	thermal_radius:			float
	def init(self):
		self.max_cluster_radius = 30
		self.tiles = "https://{s}.tile.jawg.io/jawg-matrix/{z}/{x}/{y}{r}.png?access-token=rZdfyevzxIdbsN9w6Vj7F3XIXkLO4IuXeksSMnFb8uByhftsBIHdSlCcpHVr16QR"
		self.zoom_start = 4
		self.active_hours = 3
		self.minimum_distance = 10000
		self.minimum_line_distance = 2000
		self.line_opacity = .3
		self.max_hours = 12
		self.thermal_min_opacity = .01
		self.thermal_max_zoom = 12
		self.thermal_blur = 40
		self.thermal_radius = 45


class Cfg(Prodict):
	importance_checks:	list[str]
	units:				str #m, km, mi, ft, yds. only applies to stuff being done in the web interface.
	events:				list[str]
	scan_interval:		int #seconds, how long to wait in between scans
	agencies:			list[str] #list of agency ids
	locations:			list[CfgLocation]
	default_radius:		int
	incident_filters:	Filter #global filters
	geocoder_timeout:	int #how long to wait before timing out when trying to geocode a location.
	agency_to_location_distance:	int #how far away an agency can be from a location to be considered needed for scanning (meters). default: 40km
	police_incident_tweet_count:		int
	map_config:			MapCfg
	def init(self):
		self.agency_to_location_distance = 40000
		self.importance_checks = ["textbased", "locationbased"]
		self.events = ["events_default", "events_dashboard"]
		self.default_radius = 50 #in meters
		self.scan_interval = 60 #in seconds
		self.agencies = []
		self.incident_filters = Filter()
		self.locations = []
		self.units = "m"
		self.geocoder_timeout = 9
		self.police_incident_tweet_count = 15
		self.map_config = MapCfg()







class Unit(Prodict):
	UnitID:							str
	PulsePointDispatchStatus:		str
	UnitClearedDateTime:			datetime

class Incident(Prodict):
	ID:								int
	AgencyID:						any
	Latitude:						float
	Longitude:						float
	PublicLocaiton:					int
	PulsePointIncidentCallType:		str
	IsShareable:					bool
	AlarmLevel:						int
	CallReceivedDateTime:			datetime
	ClosedDateTime:					datetime
	FullDisplayAddress:				str
	MedicalEmergencyDisplayAddress:	str #is often null, NOT RELIABLE. Use full display address instead
	AddressTruncated:				int
	Unit:							list[Unit]
	StreetNumber:					int
	CommonPlaceName:				any
	uid:							str
	incident_type:					str
	significant_locations:			list[str]
	coords:							tuple[float, float]
	agency_name:					str
	def init(self):
		self.CallReceivedDateTime = datetime(year=1990, month=1, day=1) #in case that value is null for some reason

		


class Incidents(Prodict):
	alerts:		any
	active:		list[Incident]
	recent:		list[Incident]
	def init(self):
		self.active = []
		self.recent = []
