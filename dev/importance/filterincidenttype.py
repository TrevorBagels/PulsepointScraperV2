from .. import main as M
from ..core import data as D


def check(main:M.Main, incident:D.Incident, location:M.CfgLocation) -> float:
	if location.filters.is_allowed(incident.incident_type):
		return 0 #let it pass
	else:
		return -100 #filter this out
