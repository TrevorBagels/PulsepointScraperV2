
'''
The functions in the instance class of Events are called by main.py during certain events. 
If you'd like to change how the notifications work, without falling into the dirty mess of my code, this is the place to do it.
'''
from .core import data as D
from .main import Main
from notifiers import get_notifier
class Events:
	main:	Main
	def __init__(self):
		pass
	
	#called the moment a new incident is found. this is before any analysis is done, so there won't be a 'coords' property in it
	def incident_found(self, incident:D.Incident):
		pass
	
	#called when an agency is put into the queue.
	def agency_queue_enter(self, agency:str):
		pass

	#called after an incident is analyzed, prior to notifying you (if the program decides to notify you about this particular incident, that is.)
	def incident_analyzed(self, incident):
		pass
	def main_loop_start(self):
		pass
	def main_loop_end(self):
		pass
	def analysis_start(self):
		pass
	def important_incident_found(self, incident:D.Incident, location:str, importance:int):
		pass


