from copy import deepcopy
from flask import Flask
from flask_httpauth import HTTPBasicAuth
from flask_restful import Resource, Api, reqparse

from dev.events import Events as E

from ...core import data as D
from ... import main as M
import threading, time
from itsdangerous import Serializer, TimedJSONWebSignatureSerializer, BadSignature, SignatureExpired
import hashlib
from ... import utils
from flask_cors import CORS, cross_origin



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
		#parser.add_argument('parameter', type=str, required=False) #the parameter we want to set
		args = parser.parse_args()
		params =  utils.load_json_s(args.all_parameters)
		new_config = deepcopy(self.events.main.config)
		new_config.update(params)
		print(new_config)


class GenerateToken(Resource):
	def __init__(self, events, app):
		self.events = events
		self.app = app
		pass

	def get(self): #gets a token
		parser = reqparse.RequestParser()
		parser.add_argument('password', required=True)
		args = parser.parse_args()
		password = args.password
		m = hashlib.pbkdf2_hmac('sha256', str(password).encode(), b'aoisfdhaoiS_A_L_T_asfhpasihfdosiahf', 110000)
		pwd_hash = m.hex()
		#print(pwd_hash)
		if self.events.main.keys["authentication"] == pwd_hash:
			s = Serializer(self.events.flaskapp.app.config["SECRET_KEY"])
			return s.dumps(None)
		else:
			print("Unauthorized access attempt")
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
		parser.add_argument('page', type=int, required=True)
		parser.add_argument('filter', type=str, required=False) #filter by incident type
		args = parser.parse_args()
		items = self.events.recents
		if args.filter:
			newItems = []
			for x in items:
				if x['type'].lower() == args.filter.lower(): newItems.append(x)
			items = newItems

		return items[args.count * args.page:][:args.count]


class Locations(Resource):
	def __init__(self, events:E, app):
		self.events = events
		self.app:FlaskAPI = app
		pass

	def get(self):
		if self.app.verify() == False:
			return "Unauthorized"
		return self.events.main.config.locations


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

		api.add_resource(Locations, "/locations", resource_class_kwargs={'events': self.events, 'app': self})
		api.add_resource(Incidents, "/incidents", resource_class_kwargs={'events': self.events, 'app': self})
		api.add_resource(GenerateToken, "/gettoken", resource_class_kwargs={'events': self.events, 'app': self})
		api.add_resource(Settings, "/settings", resource_class_kwargs={'events': self.events, 'app': self})
		kwargs = {"host": HOST, "port": PORT}
		if AUTO:
			kwargs = {}
		print("Starting API...")
		threading.Thread(target=self.app.run, kwargs=kwargs).start()
	def verify(self): #verifies a token
		parser = reqparse.RequestParser()
		parser.add_argument('token', required=True)
		args = parser.parse_args()
		token = args.token
		print(token)
		print("verifying...")
		s = Serializer(self.events.flaskapp.app.config["SECRET_KEY"])
		try:
			data = s.loads(token)
			print(data)
		except SignatureExpired:
			return False #token is expired
		except BadSignature:
			return False #token never existed
		return True