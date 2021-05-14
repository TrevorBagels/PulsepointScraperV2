from .. import main as M
from ..core import data as D
import re
def check(main:M.Main, incident:D.Incident, location:M.CfgLocation) -> float:
	if location.match != None:
		matches = bool(re.match(location.regex, f"{incident.FullDisplayAddress}"))
		if matches:
			return 1
		else:
			return 0
	return 0
