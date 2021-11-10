from copy import deepcopy
from os import getloadavg
from flask import Flask, Response, request
from flask_httpauth import HTTPBasicAuth
from flask_restful import Resource, Api, reqparse
from geopy import util
from geopy.distance import geodesic

from dev.events import Events as E
import datetime
from ...core import data as D
from ... import main as M
import threading, time
from itsdangerous import Serializer, TimedJSONWebSignatureSerializer, BadSignature, SignatureExpired
import hashlib
from ... import utils
from flask_cors import CORS, cross_origin


import logging



auth = HTTPBasicAuth()

#from ..events_rest_api import Events
class Settings(Resource):
	def __init__(self, events, app):
		self.events:E = events
		self.app = app
		pass

	def get(self):
		if self.app.verify() == False:
			return "Unauthorized"
		parser = reqparse.RequestParser()
		parser.add_argument('parameter', type=str, required=False) #the parameter we want to retrieve
		args = parser.parse_args()
		if args.parameter == None:
			return self.events.main.config
		else:
			return self.events.main.config[args.parameter] #internal server error will occur if supplied the wrong parameter, and im not gonna do anything about it.
	
	def post(self):
		if self.app.verify() == False:
			return "Unauthorized"
		
		parser = reqparse.RequestParser()
		parser.add_argument('all_parameters', required=True) #lets us merge new parameters
		args = parser.parse_args()
		params =  utils.load_json_s(args.all_parameters)
		#! we're gonna remove the whole tryint thing, because it's kinda dumb. instead, if we pass string values into a prodict that wants those strings to be ints,
		#! it'll convert them to ints automatically. 
		
		new_config = deepcopy(self.events.main.config.to_dict()) #copy of the current configuration as a dict
		new_config.update(params) #updated the copy of our current configuration. this is still a dict, so let's turn it into a prodict
		#if we can't turn it into a prodict, one of the values is the wrong type/format
		try:
			new_config_prodict = D.Cfg.from_dict(new_config)
		except:
			self.events.main.print("Invallid formatting for new config", t='bad')
			return "<b style='color:lightred'>INVALLID FORMAT</b>"
		
		self.events.main.config = new_config_prodict 
		self.events.save_config()
		return "<b style='color:lightgreen'>Successfully updated config!</b>"

class Map(Resource):
	def __init__(self, events, app):
		self.events:E = events
		self.app = app
	def get(self):
		if self.app.verify() == False:
			return "Unauthorized"
		else:
			map_events = self.events.main.get_event_module("map_events")
			return map_events.get_map_data();
class MapIcons(Resource):
	def __init__(self, events, app):
		self.events:E = events
		self.app = app
	def get(self):
		if self.app.verify() == False:
			return "Unauthorized"
		else:
			return utils.load_json("dev/event_modules/map_icons.json")

class GenerateToken(Resource):
	def __init__(self, events, app):
		self.events = events
		self.app:FlaskAPI = app
		pass

	def get(self): #gets a token
		parser = reqparse.RequestParser()
		parser.add_argument('password', required=True)
		args = parser.parse_args()
		password = args.password
		m = hashlib.pbkdf2_hmac('sha256', str(password).encode(), b'aoisfdhaoiS_A_L_T_asfhpasihfdosiahf', 110000)
		pwd_hash = m.hex()
		log, ip_ua = self.app.get_log_ip_ua()

		#print(pwd_hash)
		if self.events.main.keys["authentication"] == pwd_hash:
			s = Serializer(self.events.flaskapp.app.config["SECRET_KEY"])
			token = s.dumps(None)
			log['notes'] += f"Access granted\nToken:{token}\n"
			self.app.logs["long"].append(log)
			return token
		else:
			print("Unauthorized access attempt")
			log["notes"] += f"Unauthorized access attempt\nAttemped password: {password}\nHash: {pwd_hash}\n"
			self.app.logs["long"].append(log)
			return None


class Incidents(Resource):
	def __init__(self, events, app):
		self.events = events
		self.app:FlaskAPI = app
		pass

	def get(self):
		if self.app.verify() == False:
			return "Unauthorized"
		parser = reqparse.RequestParser()
		parser.add_argument('count', type=int, required=True)
		parser.add_argument('importantonly', type=bool, required=False, default=False)
		parser.add_argument('page', type=int, required=True)
		parser.add_argument('filter', type=str, required=False) #filter by incident type
		args = parser.parse_args()
		self.events.recents.sort(key= lambda x : x['epoch'], reverse=True)
		self.events.important_incidents.sort(key= lambda x : x['epoch'], reverse=True)

		items = self.events.recents
		if args.importantonly: items = self.events.important_incidents
		if args.filter:
			newItems = []
			for x in items:
				if x['type'].lower() == args.filter.lower(): newItems.append(x)
			items = newItems

		return items[args.count * args.page:][:args.count]


class IncidentsSince(Resource):
	def __init__(self, events, app):
		self.events = events
		self.app:FlaskAPI = app
	def get(self):
		if self.app.verify() == False:
			return "Unauthorized"
		parser = reqparse.RequestParser()
		parser.add_argument('time', type=str, required=True) #time in (local) YYYY-MM-DDTHH:MM:SS
		args = parser.parse_args()
		since_date = datetime.datetime.strptime(args.time, "%Y-%m-%dT%H:%M:%S").timestamp()
		
		self.events.recents.sort(key= lambda x : x['epoch'], reverse=True)

		incidents_since_time = 0
		for x in self.events.recents:
			if x["epochlocal"] >= since_date: #incident happened after this time
				incidents_since_time += 1
			else:
				break
		return {"count": incidents_since_time}
		
class EditLocation(Resource):
	def __init__(self, events:E, app):
		self.events = events
		self.app:FlaskAPI = app
	def post(self):
		if self.app.verify() == False:
			return "Unauthorized"
		parser = reqparse.RequestParser()
		parser.add_argument("location", type=str, required=True)
		parser.add_argument("method", type=str, required=True) #edit, remove
		args = parser.parse_args()
		location = utils.load_json_s(args.location)
		if args.method == "remove":
			l = self.events.main.get_location(location['name'])
			self.events.main.config.locations.remove(l)
			return "<b style='color:lightgreen;' >Location removed!</b>"
		for k, v in location.items():
			location[k] = utils.tryint(v)
		try:
			a = D.CfgLocation.from_dict(location)
		except:
			self.events.main.print("Invallid formatting for this location", t='bad')
			return "<b style='color:lightred'>INVALLID FORMAT</b>"
		index = self.events.main.config.locations.index(self.events.main.get_location(location['name']))
		self.events.main.config.locations[index] = a
		self.app.events.save_config()
		print(self.events.main.get_location(a.name))
		return "<b style='color:lightgreen'>Successfully updated config!</b>"

class Locations(Resource):
	def __init__(self, events:E, app):
		self.events = events
		self.app:FlaskAPI = app
		pass

	def get(self):
		if self.app.verify() == False:
			return "Unauthorized"
		parser = reqparse.RequestParser()
		parser.add_argument('name', type=str, required=False)
		args = parser.parse_args()
		if args.name == None:
			return self.events.main.config.locations
		else:
			return self.events.main.get_location(args.name)

	def post(self):
		if self.app.verify() == False:
			return "Unauthorized"
		parser = reqparse.RequestParser()
		parser.add_argument('name', type=str, required=True)
		parser.add_argument('address', type=str, required=False)
		parser.add_argument('lat', type=float, required=False) 
		parser.add_argument('long', type=float, required=False) 
		parser.add_argument('radius', type=float, required=False, default=self.events.main.config.default_radius)

		args = parser.parse_args()
		new_location = D.CfgLocation()
		if self.events.main.get_location(args.name) != None:
			return "<b style='color:lightred'>A location with this name already exists.</b>"
		if (args.lat == None or args.long == None) and args.address == None:
			return "<b style='color:lightred'>You must supply coordinates or an address</b>"
		try: #convert from strings to proper format, if it doesn't work, respond with an error lookin thing
			new_location.name = args.name
			new_location.radius = int(args.radius)
			new_location.address = args.address
			if args.lat != None and args.long != None:
				new_location.coords = [float(args.lat), float(args.long)] #set coords
			else:
				new_location.coords = self.events.main.get_coords(new_location.address) #set coords
		except:
			return "<b style='color:lightred'>Invallid Format</b>"

		
		# at this point, the address and/or coords have been set. 
		if new_location.coords != None: #find nearby agencies and add them
			for i, a in self.events.agency_data.items():
				if a == None or a["agency"] == None: continue
				coords = (float(a["agency"]["agency_latitude"]), float(a["agency"]["agency_longitude"]))
				if geodesic(coords, new_location.coords).meters < self.events.main.config.agency_to_location_distance:
					if a["agency"]["agencyid"] not in self.events.main.config.agencies:
						self.events.main.config.agencies.append(a["agency"]["agencyid"])
		self.events.main.config.locations.append(new_location)
		self.app.events.save_config()
		return "<b style='color:lightgreen'>Location sucessfully created!</b>"

class IpLogs(Resource):
	def __init__(self, events:E, app):
		self.events = events
		self.app:FlaskAPI = app
	def get(self):
		if self.app.verify() == False:
			return "Unauthorized"
		parser = reqparse.RequestParser()
		parser.add_argument('count', type=int, required=True)
		parser.add_argument('kind', type=str, required=True) #long, short, ip_ua
		args = parser.parse_args()
		logs = self.app.logs[args.kind][:args.count]
		return logs

class Authorized(Resource):
	def __init__(self, events:E, app):
		self.events = events
		self.app:FlaskAPI = app
		pass
	def get(self):
		if self.app.verify() == False:
			return "Unauthorized"
		else:
			return "Authorized"



HOST = "0.0.0.0"
PORT = "5001"
AUTO = False

class FlaskAPI:
	def __init__(self, events):
		from ..events_rest_api import Events
		self.events:Events = events
		print("setting up app")
		self.app = Flask(__name__)
		self.app.config["SECRET_KEY"] = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' #they'll never guess this
		print("setting up API")
		api = Api(self.app)
		cors = CORS(self.app)
		self.app.config['CORS_HEADERS'] = 'Content-Type'
		self.load_logs()
		logging.getLogger('werkzeug').setLevel(logging.ERROR)

		api.add_resource(Locations, "/locations", resource_class_kwargs={'events': self.events, 'app': self})
		api.add_resource(EditLocation, "/locations/edit", resource_class_kwargs={'events': self.events, 'app': self})
		api.add_resource(Map, "/map", resource_class_kwargs={'events': self.events, 'app': self})
		api.add_resource(MapIcons, "/mapicons", resource_class_kwargs={'events': self.events, 'app': self})
		api.add_resource(Incidents, "/incidents", resource_class_kwargs={'events': self.events, 'app': self})
		api.add_resource(GenerateToken, "/gettoken", resource_class_kwargs={'events': self.events, 'app': self})
		api.add_resource(Settings, "/settings", resource_class_kwargs={'events': self.events, 'app': self})
		api.add_resource(Authorized, "/checkauth", resource_class_kwargs={'events': self.events, 'app': self})
		api.add_resource(IncidentsSince, "/incidents/since", resource_class_kwargs={'events': self.events, 'app': self})
		api.add_resource(IpLogs, "/logs", resource_class_kwargs={'events': self.events, 'app': self})
		kwargs = {"host": HOST, "port": PORT}
		if AUTO:
			kwargs = {}
		print("Starting API...")
		threading.Thread(target=self.app.run, kwargs=kwargs).start()
	
	def load_logs(self):
		self.logs = utils.load_json("dev/event_modules/flask/logs.json") or {"short": [], "long": [], "ip_ua": []}
	def save_logs(self):
		utils.save_json("dev/event_modules/flask/logs.json", self.logs)
	def get_log_ip_ua(self):
		log = {"time": utils.local(utils.now()).strftime("%Y-%m-%dT%H:%M:%S.%f"), "port": request.environ["REMOTE_PORT"], "ip": request.environ['REMOTE_ADDR'], "ua": request.environ['HTTP_USER_AGENT'], "method": request.environ['REQUEST_METHOD'], "uri": request.environ["RAW_URI"], "notes": ""}
		ip_ua = ip_ua = str(log["ip"]) + "__" + str(log["ua"])
		if ip_ua not in self.logs['ip_ua']:
			self.logs['ip_ua'].append(ip_ua)
			self.logs['long'].append(log)
		self.logs['short'].insert(0, log)
		return log, ip_ua
	def verify(self): #verifies a token
		log, ip_ua = self.get_log_ip_ua()
		#determine if this should go in the logs or not
		#actually, it'll go in the logs if the access attempt is bad, it's a new IP, or a new user agent
		parser = reqparse.RequestParser()
		parser.add_argument('token', required=True)
		args = parser.parse_args()
		token = args.token
		s = Serializer(self.events.flaskapp.app.config["SECRET_KEY"])
		try:
			data = s.loads(token)
		except SignatureExpired:
			log['notes'] += "Signature Expired\n"
			return False #token is expired
		except BadSignature:
			log['notes'] += "Bad Signature\n"
			return False #token never existed
		log['notes'] += "Authorized\n"
		return True