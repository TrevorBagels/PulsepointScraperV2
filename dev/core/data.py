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
	def init(self):
		self.name = ""
		self.address = ""
		self.radius = 50
		self.importance = 1
		self.match = None
		self.filters = Filter()


class Cfg(Prodict):
	importance_checks:	list[str]
	units:				str #m, km, mi, ft, yds. only applies to stuff being done in the web interface.
	events:				list[str]
	scan_interval:		int #seconds, how long to wait in between scans
	agencies:			list[str] #list of agency ids
	locations:			list[CfgLocation]
	default_radius:		int
	incident_filters:	Filter #global filters
	agency_to_location_distance:	int #how far away an agency can be from a location to be considered needed for scanning (meters). default: 40km
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
	MedicalEmergencyDisplayAddress:	str
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
