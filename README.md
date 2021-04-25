# PulsepointScraperV2
Scrapes pulsepoint.org for emergency incidents and notifies you if certain conditions are met.



## Installation
1. Clone the repository `git clone https://github.com/TrevorBagels/PulsepointScraperV2.git`
2. Navigate to the new directory `cd PulsepointScraperV2`
3. Install requirements `pip3 install -r requirements.txt`
4. Make sure to configure before using!


## Configuration

To use google maps API, you'll need to supply an api key to "api_key" in the config. Otherwise, it'll do its best to use other options for geocoding addresses. 

For push notifications, you'll need [pushover](https://pushover.net/). Set the "pushover_token" and "pushover_user" to the application token and user token for your pushover account.


[old configuration](https://github.com/TrevorBagels/PulsepointScraper/wiki/Configuration)

## Usage
Run `python3 -m dev`, and it should work.


## FAQ

Not that there are many people that ask me questions about this, but I'll go head and answer things I have been asked, and what I think people *will* ask.

* Q: The incidents are showing up in the console, but I don't get notified about them. Why?
  * A: The incidents you see in the console are ALL of the incidents for the agencies you are monitoring. To get notified, there needs to be a location properly configured. If an incident happens near that location, you'll be notified. If you'd like to monitor an entire city, create a location, setting the `"coords"` property of it to be the center of the city. Then, set the `"radius"` property to something like `"50mi"` (50 miles). Units, such as meters (`m`), kilometers (`km`), and feet (`ft`) work as well. The default radius, if none is set, defaults to 100 meters.
* Q: The program isn't finding the agency, how do I fix this?
  * A: Chances are, the agency doesn't exist, or you mistyped something. Check `agencies.txt` for a list of agencies. You can do a search in there to find the exact name for the agency you want to monitor.
