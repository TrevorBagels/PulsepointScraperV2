import json, time, os, re
from bson import json_util
from datetime import date, datetime, timezone, timedelta
import traceback


def to_iso8601(dt:datetime):
	return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
def from_iso8601(dt:str) -> datetime:
	if type(dt) == datetime: return dt
	return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%SZ').astimezone(timezone.utc)

def save_json(file, data:dict):
	write_to(file, json.dumps(data, indent=4, default=json_util.default))

def load_json(file) -> dict:
	if os.path.exists(file) == False:
		write_to(file, "{}") #make that file exist, and give it nothing.
	return json.loads(read(file), object_hook=json_util.object_hook)

def write_to(file, content):
	with open(file, "w+") as f:
		f.write(content)

def read(file):
	t = ""
	with open(file, "r") as f:
		t = f.read()
	return t


def get(items:list[dict], value, a='name'):
	for x in items:
		if value in x:
			if type(value) == str and bool(re.match(value, x[value])):
				return x
			else:
				if x[value] == value:
					return x
	return None


def round_to_nearest(num, base):
	n = num + (base//2)
	return n - (n % base)

def now() -> datetime:
	return datetime.now().astimezone(timezone.utc).replace(tzinfo=None)

def local(t:datetime) -> datetime:
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return t + offset


def long_ago() -> datetime:
	return datetime(1990, 1, 1).astimezone(timezone.utc)

def hms(seconds):
	"""Returns h:m:s from seconds
	"""
	seconds = seconds % (24 * 3600)
	hour = seconds // 3600
	seconds %= 3600
	minutes = seconds // 60
	seconds %= 60
	return "%d:%02d:%02d" % (hour, minutes, seconds)

def dhms(seconds):
	"""Returns d days, h:m:s from seconds
	"""
	days = seconds // 86400
	seconds = seconds % (24 * 3600)
	hour = seconds // 3600
	seconds %= 3600
	minutes = seconds // 60
	seconds %= 60
	return  f"{days} day(s), " + "%d:%02d:%02d" % (hour, minutes, int(seconds))

def time_elapsed(seconds):
	if seconds < 60:
		return f"{'%02d' % seconds}s"
	minutes = seconds // 60
	if minutes < 60:
		return f"{'%02d' % minutes}m {'%02d' % (seconds - minutes*60)}s"
	return hms(seconds)

def pluralize(word, value, plural=None, include_value=True):
	if include_value: word = str(value) + " " + word
	if plural == None: plural = word + "s"
	if float(value) == 1.0: return word
	return plural

def time_elapsed_1(seconds):
	if seconds < 60:
		return pluralize("second", int(seconds))
	minutes = seconds // 60
	if minutes < 60:
		return f"{'%02d' % round(minutes + seconds/60, 1)} minutes"
	hours = minutes // 60
	if hours < 24:
		return f"{'%02d' % round(hours + minutes/60, 1)} hours"
	days = hours // 24

	return f"{pluralize('day', days)}, " + f"{'%02d' % round(hours + minutes/60, 1)} hours"

def round_seconds_datetime(dt: datetime) -> datetime:
    if dt.microsecond >= 500_000:
        dt += timedelta(seconds=1)
    return dt.replace(microsecond=0)

def round_seconds_delta(dt: timedelta) -> timedelta:
    if dt.microseconds >= 500_000:
        dt += timedelta(seconds=1, microseconds=-dt.microseconds)
    return dt


def utc2local(utc) -> datetime:
	epoch = time.mktime(utc.timetuple())
	offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
	return utc + offset