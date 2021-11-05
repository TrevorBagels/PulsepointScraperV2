
'''
This one creates a webmap of all the recent incidents
Note that this is an example of what you can do with the events class, and this requires changing some things for practical use

'''
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



class Events(events.Events):
	def __init__(self):
		super().__init__()

	def post_init(self):
		self.savePath = "./"
		
		self.location = self.main.config.locations[0]['coords'] #center point for the location
		d = .1
		self.sw = [self.location[0] - d, self.location[1] - d]
		self.ne = [self.location[0] + d, self.location[1] + d]
		self.logFileName = "Logs/" + str(datetime.datetime.now()).split(" ")[0] + "_" + str(random.randrange(1, 9999)) + ".log"
		self.incidents = []
		print(self.location)
		self.map = folium.Map(location=self.location, zoom_start=4, tiles="https://{s}.tile.jawg.io/jawg-matrix/{z}/{x}/{y}{r}.png?access-token=rZdfyevzxIdbsN9w6Vj7F3XIXkLO4IuXeksSMnFb8uByhftsBIHdSlCcpHVr16QR", attr="<a>somethin should go here</a>") #"https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
		#these coords are the bottom left and top right points for the viewport
		self.drawLines = True
	
	#called after an incident is analyzed, prior to notifying you (if the program decides to notify you about this particular incident, that is.)
	def incident_analyzed(self, incident:D.Incident):
		#determine marker icon
		self.incidents.append(incident)
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
			"Odor Investigation": "|pink",
			"Hazardous Condition": "|pink",
			"Investigation": "question|darkgreen",
			"Lockout": "lock|darkblue",
			"Commercial Fire": "fire|red",
			"Carbon Monoxide": "smoke|gray",
			"Alarm": "alarm|darkblue",
			"Lift Assist": "plane|darkpurple",
			"Water Rescue": "tint|pink",
			"Public Service": "|cadetblue",
			"Electrical Emergency": "bolt|red",
			"Wires Arcing": "bolt|yellow",
			"Rescue": "parachute-box|red",
			"Gas Leak": "smog|pink"

		}
		if incident.incident_type in icons:
			icon = icons[incident.incident_type]
		
		if 'fire' in incident.incident_type.lower():
			icon = icons["Outside Fire"]
		color = "lightgreen"
		if len(icon.split("|")) == 2:
			a =  icon.split("|")
			color = a[1]
			icon = a[0]
		useIcon = folium.Icon(color=color, icon=icon, prefix='fa') #the icon to actually use
		#make a marker of this incident
		#draws a line to the nearest monitored location. looks pretty cool.
		cancel_marking = False
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
			if closestDist > 12000:
				return
			points = [tuple(p1), tuple(self.main.config.locations[closest].coords)]
			folium.PolyLine(points, color="red", weight=2.5, opacity=.3).add_to(self.map)
			folium.Marker(icon=useIcon, location=incident.coords, tooltip=incident.incident_type, popup=f'<p>{incident.CallReceivedDateTime.strftime("%M/%d, %H:%M")}<br>{incident.FullDisplayAddress}</p>').add_to(self.map)
		pass

	def main_loop_end(self):#save the latest map
		self.map.fit_bounds([self.sw, self.ne])
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
