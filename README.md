# PulsepointScraperV2
Scrapes pulsepoint.org for emergency incidents and notifies you if certain conditions are met.



## Installation
1. Clone the repository `git clone https://github.com/TrevorBagels/PulsepointScraperV2.git`
2. Navigate to the new directory `cd PulsepointScraperV2`
3. Install requirements `pip3 install -r requirements.txt`
4. Make sure to configure before using!


## Configuration

To use google maps API, you'll need to supply an api key to "api_key" in the config. Otherwise, it'll do it's best to use other options for geocoding addresses. 

For push notifications, you'll need [pushover](https://pushover.net/). Set the "pushover_token" and "pushover_user" to the application token and user token for your pushover account.


[old configuration](https://github.com/TrevorBagels/PulsepointScraper/wiki/Configuration)

## Usage
Simply run `python3 main.py` and everything should work.
