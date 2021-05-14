#big thanks to this right here: https://gist.github.com/Davnit/4a6e7dd94d97a05c3806b306e3d838c6
#I modified most of the code to fit into this class
import base64
import hashlib
import json
from urllib import request
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from . import data as D
import datetime
class Scraper:
	def __init__(self):
		self.agencies = {}
		self.incident_types = {}
		with open("./dev/core/incident_types.json") as f:
			self.incident_types = json.loads(f.read())
		agenciesJSON = requests.get("https://web.pulsepoint.org/DB/GeolocationAgency.php").json()["agencies"]
		for x in agenciesJSON:
			self.agencies[x['agencyid']] = x

	def str2time(self, s):
		#"2021-03-28T18:56:16Z
		return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")

	def get_incidents(self, a_id) -> D.Incidents:
		def fix_dict(d):
			if d == 'null': return None
			if isinstance(d, dict):
				for k, v in d.items():
					d[k] = fix_dict(v)
			if isinstance(d, list):
				for i, v in enumerate(d):
					d[i] = fix_dict(v)
			return d
		def convert_incidents(i_list):
			if type(i_list) != list: return
			conversions = ["CallReceivedDateTime", "ClosedDateTime", "UnitClearedDateTime"]
			for i, x in enumerate(i_list):
				for c in conversions:
					if c in x and type(x[c]) == str:
						x[c] = self.str2time(x[c])
				if "Unit" in x:
					convert_incidents(x["Unit"])
				if "PulsePointIncidentCallType" in x:
					x["incident_type"] = self.incident_types[x["PulsePointIncidentCallType"]]
				if "Latitude" in x:
					x['coords'] = (float(x['Latitude']), float(x['Longitude']))
					x['uid'] = x['ID']
		raw = None
		try:
			raw = self._agency_raw_data(a_id)['incidents']
			convert_incidents(raw['active'])
			convert_incidents(raw['recent'])
			fix_dict(raw)
		except Exception as e:
			print(e)
			return D.Incidents()
		
		return D.Incidents.from_dict(raw)

	
	def _agency_raw_data(self, a_id):
		data = json.loads(request.urlopen(f"https://web.pulsepoint.org/DB/giba.php?agency_id={a_id}").read().decode())
		ct = base64.b64decode(data.get("ct"))
		iv = bytes.fromhex(data.get("iv"))
		salt = bytes.fromhex(data.get("s"))
		# Build the password
		t = ""
		e = "CommonIncidents"
		t += e[13] + e[1] + e[2] + "brady" + "5" + "r" + e.lower()[6] + e[5] + "gs" #No idea why, but ok. 
		# Calculate a key from the password
		hasher = hashlib.md5()
		key = b''
		block = None
		while len(key) < 32:
			if block:
				hasher.update(block)
			hasher.update(t.encode())
			hasher.update(salt)
			block = hasher.digest()
			hasher = hashlib.md5()
			key += block
		# Create a cipher and decrypt the data
		backend = default_backend()
		cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
		decryptor = cipher.decryptor()
		out = decryptor.update(ct) + decryptor.finalize()
		out = out[1:out.rindex(b'"')].decode()
		out = out.replace(r'\"', r'"')
		return json.loads(out)
	
	def get_agency(self, name) -> dict:
		for i, x in self.agencies.items():
			options = ["id", "agency_initials", "agencyname", "short_agencyname"]
			for o in options:
				if o in x and str(x[o]).lower() == str(name).lower(): return x
		print(f"FAILED TO FIND AGENCY \"{name}\". Looking for the closest match!")
		for i, x in self.agencies.items():
			options = ["id", "agency_initials", "agencyname", "short_agencyname"]
			for o in options:
				if o in x and (str(x[o]).lower() in str(name).lower() or str(name).lower() in str(x[o]).lower()): 
					print(f"Using \"{x['agencyname']}\" instead!")
					return x
		return None


#? For testing purposes
"""
from core import scrape
s = scrape.Scraper()
a = s.get_incidents("03101")
"""