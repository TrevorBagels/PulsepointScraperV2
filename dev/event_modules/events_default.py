from .. import events, utils
from ..core import data as D
from notifiers import get_notifier
from geopy.distance import geodesic
class Events(events.Events):
	#called the moment a new incident is found. this is before any analysis is done, so there won't be a 'coords' property in it
	def incident_found(self, incident:D.Incident):
		#self.main.print(f"{incident.incident_type} found at {incident.FullDisplayAddress}.", incident.coords, end='\r')
		pass
	#called when an agency is put into the queue.
	def agency_queue_enter(self, agency:str):
		self.main.print(f"Added agency {agency} to the queue.", t='good', end='\r')
		pass
	def analysis_start(self):
		pass
	def analysis_end(self):
		pass
	
	def important_incident_found(self, incident:D.Incident, location:D.CfgLocation, importance:int):
		p = get_notifier("pushover")
		address = ""
		if location.address != None: address = location.address
		distance = "N/A"
		if incident.dists != None and location.name in incident.dists: distance = incident.dists[location.name]
		message = f"""{incident.incident_type.upper()} AT {location.name.upper()}
	Time:				{utils.local(incident.CallReceivedDateTime).strftime("%a, AT %H:%M")}
	Incident Address:		{incident.FullDisplayAddress.upper()}
	Monitored address:		{address.upper()}
	Incident coords:		{incident.coords}
	Distance:			{"%03d" % distance} meters""".upper()

		self.main.print(message, t='important')
		p.notify(user=self.main.keys["pushover_user"], token=self.main.keys["pushover_token"], message=message)
		pass


#custom helper method
def GetLocationByName(main, name):
	for x in main.config['locations']:
		if x['name'] == name:
			return x
	main.print(f'could not find location using name "{name}"', t='bad')
