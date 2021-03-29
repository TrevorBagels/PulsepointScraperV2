from ..prodict import Prodict
from datetime import datetime
class Unit(Prodict):
	UnitID:							str
	PulsePointDispatchStatus:		str
	UnitClearedDateTime:			datetime

class Incident(Prodict):
	ID:								int
	AgencyID:						int
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
