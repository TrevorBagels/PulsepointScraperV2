import requests
from bs4 import BeautifulSoup
import datetime

txt = requests.get("https://www.pdxpolicelog.com/")

soup = BeautifulSoup(txt)

unparsed = soup.find_all("div", {"class": "rt-BaseCard"})

for x in unparsed:
	#each of these has incident data
	x1 = x.find("div")
	title = x1.find('h2').text.split("at")
	incident_type = title[0].strip()
	locationDesc = title[1].strip()
	t = x1.find("span").text.split(" ") #time May 18, 2025, 10:31:30 AM
	months = {"January": 1, "Feburary": 2, "March": 3, "April": 4, "May": 5, "June": 6, "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}
	month = months[t[0]]
	day = int(t[1].split(",")[0])
	year = int(t[2].split(",")[0])
	tt = t[3].split(":")
	h = int(tt[0])
	if t[4] == "PM": h += 12
	if h == 24: h = 0
	m = int(tt[1])
	date = datetime.datetime(year, month, day, h, m)
	#date = utils.local_to_utc(date).replace(tzinfo=None) #convert to UTC
	
	coordsUnparsed = x1.find("a").get("href").split("query=")[1].split(",")
	coords = [float(coordsUnparsed[0].strip()), float(coordsUnparsed[1].strip())]


	

