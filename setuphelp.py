from cmd import Cmd
import json
from dev.main import Cfg, CfgLocation
from dev.core import scrape
class Main(Cmd):
	def __init__(self):
		super().__init__()
		self.agencies = []
		self.scraper = scrape.Scraper()
		for k,v in self.scraper.agencies.items():
			self.agencies.append(v["agencyname"])

		with open("config.json", "r") as f:
			self.cfg = json.loads(f.read())
	def input(self, txt):
		return input(str(txt) + ":\t")
	def do_place(self):
		name = self.input("Location name")
		address = self.input("Address")
		self.cfg['locations'].append({"name": name, "address": address})
		print("Location added.")
		self.save()
	
	def do_agency(self, name):
		thisname = name
		for x in self.agencies:
			if x.lower().startswith(name): thisname = x
		self.cfg['agencies'].append({'name': thisname})
		print(f"Agency {thisname} added.")
		self.save()
	
	def save(self):
		with open("config.json", "w+") as f:
			f.write(json.dumps(self.cfg, indent=4))


	def complete_agency(self, text, line, begidx, endidx):
		if not text:
			return self.agencies[:]
		else:
			return [a for a in self.agencies if a.lower().startswith(text.lower)]
	def do_EOF(self, line):
		return True

if __name__ == "__main__":
	Main().cmdloop()