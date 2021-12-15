from ..prodict import Prodict
from datetime import datetime
class Unit(Prodict):
	UnitID:							str
	PulsePointDispatchStatus:		str
	UnitClearedDateTime:			datetime

class Filter(Prodict):
	allowed:		list[str]
	blocked:		list[str] #a "*" will apply to all items
	def init(self):
		self.allowed = []
		self.blocked = []
	
	def is_allowed(self, item):
		if len(self.blocked) == 0 and len(self.allowed) == 0: return True #no filters in place

		if len(self.blocked) == 0: #nothing in the block-list, but things ARE in the allow-list. 
			return item in self.allowed or "*" in self.allowed
		elif len(self.allowed) == 0: #nothing in the allow-list, but things ARE in the block-list
			return item not in self.blocked and "*" not in self.blocked
		else: #the allow-list has things, and so does the block-list
			return (item in self.allowed) and (item not in self.blocked)
	
	
	
	





class Incident(Prodict):
	ID:								int
	AgencyID:						str
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

		


class Incidents(Prodict):
	alerts:		any
	active:		list[Incident]
	recent:		list[Incident]
	def init(self):
		self.active = []
		self.recent = []
