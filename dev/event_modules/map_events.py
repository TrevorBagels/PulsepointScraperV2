
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
from geopy.distance import geodesic
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
		print(self.location)
		self.init_map()
	
	def init_map(self):
		#tiles = "stamentoner"
		tiles = "https://{s}.tile.jawg.io/jawg-matrix/{z}/{x}/{y}{r}.png?access-token=rZdfyevzxIdbsN9w6Vj7F3XIXkLO4IuXeksSMnFb8uByhftsBIHdSlCcpHVr16QR"
		self.map = folium.Map(location=self.location, zoom_start=4, tiles=tiles, attr="<a>somethin should go here</a>") #"https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
		self.markers = MarkerCluster(options={"maxClusterRadius": 30, "animate": True, "spiderfyOnMaxZoom": True, "spiderLegPolylineOptions": {"weight": 3, "color": "#00f", "opacity": 1}}).add_to(self.map)
		#these coords are the bottom left and top right points for the viewport
		self.drawLines = True

	#called after an incident is analyzed, prior to notifying you (if the program decides to notify you about this particular incident, that is.)
	def incident_analyzed(self, incident):
		self.incidents.append(incident)
	
	def add_incident_to_map(self, incident:D.Incident):
		#determine marker icon
		icon = "map-marker"
		icons = {
			"Medical Emergency": "heartbeat|blue",
			"Outside Fire": "fire|red",
			"Residential Fire": "home|red",
			"Vehicle Fire": "fire|red",
			"Illegal Fire": "fire|darkred",
			"Fire Alarm": " fire-extinguisher|red",
			"Interfacility Transfer":"bus",
			"Traffic Collision": "car|orange",
			"Odor Investigation": "sellsy|pink",
			"Hazardous Condition": "biohazard|pink",
			"Investigation": "question|darkgreen",
			"Lockout": "lock|darkblue",
			"Commercial Fire": "fire|red",
			"Carbon Monoxide": "smoke|gray",
			"Alarm": "alarm|darkblue",
			"Lift Assist": "plane|darkpurple",
			"Water Rescue": "tint|pink",
			"Public Service": "|cadetblue",
			"Electrical Emergency": "bolt|red",
			"Wires Arcing": "bolt|orange",
			"Rescue": "parachute-box|red",
			"Gas Leak": "smog|pink",
			"Explosion": "bomb|pink",
			"Violence": "exclamation|red",
			"Suspicious Activity": "user-secret|darkpurple",
			"Unwanted Person": "user-times|darkpurple",
			"Noise Disturbance": "volume-up|darkgreen",
			"Hazmat Response": "biohazard|pink",
			"Elevator Rescue": "grip-lines-vertical|blue",
			"Trimet": "train|cadetblue",
			"Theft": "mask|darkred"
		}
		if incident.incident_type in icons:
			icon = icons[incident.incident_type]
		itype = incident.incident_type.lower()
		if 'fire' in itype: icon = icons["Outside Fire"]
		if "shots" in itype or "shooting" in itype or "threat" in itype or "stabbing" in itype or "vio" in self.main.incident_type_tags[incident.incident_type]:
			icon = icons["Violence"]
		if "theft" in itype:
			icon = icons["Theft"]
		if "suspicious" in itype: icon = icons["Suspicious Activity"]
		if "disturbance" in itype: icon = icons["Noise Disturbance"]
		if "trimet" in itype: icon = icons["Trimet"]
		color = "lightgreen"
		if len(icon.split("|")) == 2:
			a =  icon.split("|")
			color = a[1]
			icon = a[0]
		time_ago = ((utils.now() - incident.CallReceivedDateTime).total_seconds() / 60 / 60)
		if time_ago > 3:
			color = "gray"
		useIcon = folium.Icon(color=color, icon=icon, prefix='fa') #the icon to actually use
		#make a marker of this incident
		#draws a line to the nearest monitored location. looks pretty cool.
		if self.drawLines:
			p1 = incident.coords
			closest = 0
			closestDist = 100000 #meters
			for l, i in zip(self.main.config.locations, range(len(self.main.config.locations))):
				if l.coords != None and incident.coords != None:
					dist = hs.haversine(l.coords, incident.coords, unit=hs.Unit.METERS)
					if dist < closestDist:
						closest = i
						closestDist = dist
			if closestDist > 15000:
				return
			if closestDist < 4000:
				points = [tuple(p1), tuple(self.main.config.locations[closest].coords)]
				folium.PolyLine(points, color=color, weight=1.5, opacity=.3).add_to(self.markers)
			mkr = folium.Marker(icon=useIcon, location=incident.coords, 
				tooltip=incident.incident_type, 
				popup=f'<p>{utils.local(incident.CallReceivedDateTime).strftime("%a, %H:%M").upper()}<br>{incident.FullDisplayAddress}</p>')
			if "vio" in self.main.incident_type_tags[incident.incident_type] or "theft" in self.main.incident_type_tags[incident.incident_type]:
				mkr.add_to(self.map)
			else:
				mkr.add_to(self.markers)
		pass

	def main_loop_end(self):#save the latest map
		remove = []
		for x in self.incidents:
			if ((utils.now() - x.CallReceivedDateTime).total_seconds() / 60 / 60) > 12:
				remove.append(x)
		for x in remove: self.incidents.remove(x)
		self.init_map()
		heatMapPoints = []
		for x in self.incidents:
			self.add_incident_to_map(x)
			if "vio" in self.main.incident_type_tags[x.incident_type] or "theft" in self.main.incident_type_tags[x.incident_type]:
				heatMapPoints.append(x.coords)
		self.map.fit_bounds([self.sw, self.ne])
		self.map.add_child(HeatMap(heatMapPoints, name="Heat map", radius=45, blur=40, max_zoom=12, min_opacity=0))
		
		self.map.save(self.savePath + "map.html")
		#refresh the uberschit widget. commented out because most people probably don't use uberschit
		'''
		with open("/Users/bagel/Library/Application Support/Übersicht/widgets/bagel.widget/pulsepointmap.coffee", "r+") as f:
			f.write("")
		with open(self.logFileName, "w+") as f:
			f.write(json.dumps(self.incidents))
		'''




def GetLocationByName(main, name):
	for x in main.config['locations']:
		if x['name'] == name:
			return x
	print(f'could not find location using name "{name}"')
