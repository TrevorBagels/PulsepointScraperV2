from .. import main as M
from ..core import data as D

def check(main:M.Main, incident:D.Incident, location:M.CfgLocation) -> bool:
	if location.match != None:
		matchString = removeChars(location.match.lower()) #the monitored location matching string (if this is in the incident, then it's important)
		if matchString in removeChars(incident.FullDisplayAddress.lower()): #there was a text match, this is important
			return True
	return False



def removeChars(txt, chars=",./?><()+=-_~!#"):
		newTxt = txt
		for x in chars:
			newTxt = newTxt.replace(x, "")
		return newTxt