
'''
This one creates a webmap of all the recent incidents
Note that this is an example of what you can do with the events class, and this requires changing some things for practical use

'''
from folium.map import LayerControl
import numpy as np
import pandas as pd
from notifiers import get_notifier
import folium
import haversine as hs
import json, datetime, random
from .. import events
from ..core import data as D
from geopy.distance import GeodesicDistance, geodesic
import pandas as pd
from .. import utils

from folium.plugins import HeatMap, MarkerCluster

class Events(events.Events):
	def __init__(self):
		super().__init__()

	def post_init(self):
		self.savePath = "./"
		
		self.location = self.main.config.locations[0]['coords'] #center point for the location
		d = .1
		self.sw = [self.location[0] - d, self.location[1] - d]
		self.ne = [self.location[0] + d, self.location[1] + d]
		self.incidents:list[D.Incident] = []
	

	#called after an incident is analyzed, prior to notifying you (if the program decides to notify you about this particular incident, that is.)
	def incident_found(self, incident):
		self.incidents.append(incident)
	
	def get_incident_marker_icon(self, incident:D.Incident) -> tuple[str, bool]: #returns [iconname, old]
		icon = "default"
		icons = utils.load_json("dev/event_modules/map_icons.json")
		itype = incident.incident_type.lower()
		if 'fire' in itype: icon = "Outside Fire"
		
		if incident.incident_type.title() in icons:
			icon = incident.incident_type.title()
		
		if "shots" in itype or "shooting" in itype or "stabbing" in itype or "vio" in self.main.incident_type_tags[incident.incident_type]:
			icon = "Violence"
		if "threat" in itype: icon = "Threat"
		if "assault" in itype: icon = "Assault"
		if "shots" in itype or "shooting" in itype or "weapon" in itype: icon = "Armed Violence"
		if "theft" in itype: icon = "Theft"
		if "burglary" in itype: icon = "Break In"
		if "robbery" in itype: icon = "Theft"
		if "unwanted person" in itype: icon = "Unwanted Person"
		if "hazard" in itype: icon = "Hazmat Response"
		if "suspicious" in itype: icon = "Suspicious Activity"
		if "disturbance" in itype: icon = "Noise Disturbance"
		if "vandalism" in itype: icon = "Vandalism"
		if "accident" in itype: icon = "Accident"
		if "hit and run" in itype: icon = "Hit and Run"
		if "trimet" in itype: icon = "Trimet"
		time_ago = ((utils.now() - incident.CallReceivedDateTime).total_seconds() / 60 / 60)
		old = False
		if time_ago > self.main.config.map_config.active_hours:
			old = True
		return icon, old

	def get_incident_marker_data(self, incident:D.Incident):
		iconname, old = self.get_incident_marker_icon(incident)
		location = incident.coords
		tooltip = incident.incident_type
		popup = f'<p>{utils.local(incident.CallReceivedDateTime).strftime("%a, %H:%M").upper()}<br>{incident.FullDisplayAddress}</p>'
		target = "markercluster"
		if "vio" in self.main.incident_type_tags[incident.incident_type] or "theft" in self.main.incident_type_tags[incident.incident_type]:
			target = "map"
		line, draw = self.get_incident_lines(incident)
		return {"iconname": iconname, "old": old, "location": location, "tooltip": tooltip, 
			"popup": popup, "target": target, 
			"line": line,
			"draw": draw,
			"heat": ("vio" in self.main.incident_type_tags[incident.incident_type] or "theft" in self.main.incident_type_tags[incident.incident_type])}


	def get_incident_lines(self, incident:D.Incident) -> tuple[tuple, bool]: #points, draw
		points = None
		p1 = incident.coords
		closest = 0
		closestDist = 100000 #meters
		for l, i in zip(self.main.config.locations, range(len(self.main.config.locations))):
			if l.coords != None and incident.coords != None:
				dist = hs.haversine(l.coords, incident.coords, unit=hs.Unit.METERS)
				if dist < closestDist:
					closest = i
					closestDist = dist
		if closestDist > self.main.config.map_config.minimum_distance:
			return (None, False)
		if closestDist <= self.main.config.map_config.minimum_line_distance:
			#points = [tuple(p1), tuple(self.main.config.locations[closest].coords)]
			points = tuple(self.main.config.locations[closest].coords)
		return (points, True)

	def main_loop_end(self):
		#remove old incidents
		remove = []
		for x in self.incidents:
			if ((utils.now() - x.CallReceivedDateTime).total_seconds() / 60 / 60) > self.main.config.map_config.max_hours: remove.append(x)
		for x in remove: self.incidents.remove(x)
	
	def get_map_data(self) -> list[dict]:
		data = []
		for x in self.incidents:
			if ((utils.now() - x.CallReceivedDateTime).total_seconds() / 60 / 60) <= self.main.config.map_config.max_hours:
				data.append(self.get_incident_marker_data(x))
		return data