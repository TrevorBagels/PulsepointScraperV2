from .. import main as M
from ..core import data as D
import re
def check(main:M.Main, incident:D.Incident, location:D.CfgLocation) -> float:
	if location.match != None and location.match != "":
		matches = bool(re.match(location.match, f"{incident.FullDisplayAddress}")) #changed re.match(location.regex... to re.match(location.match because locations don't have a "regex" property
		if matches:
			return 1
		else:
			return 0
	return 0
