from .. import main as M
from ..core import data as D
from geopy.distance import geodesic

def check(main:M.Main, incident:D.Incident, location:M.CfgLocation) -> float:
	if 'dists' not in incident: incident['dists'] = {}
	if location.coords != None:
		incident.dists[location.name] = geodesic(incident.coords, location.coords).meters
		if incident.dists[location.name] <= location.radius:
			return incident.dists[location.name] / location.radius
	return 0
