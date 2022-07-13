# PulsepointScraperV2
Scrapes pulsepoint.org for emergency incidents and notifies you if certain conditions are met.

# Setting up Pulsepoint Monitor with web interface

1. Clone the repository (V3 branch) `git clone --branch V3 https://github.com/TrevorBagels/PulsepointScraperV2.git`
2. Navigate to the new directory `cd PulsepointScraperV2`
3. Install requirements `pip3 install -r requirements.txt`
4. Run `python3 -m dev`

# Web interface
To enable the web app, you'll need to use Jekyll. If you have Jekyll installed, you should be able to run the web interface by running `bundle exec jekyll serve -H 0.0.0.0` from the `/site` directory after running `bundle install` in the same directory. 

Navigate to `0.0.0.0:4000` and your interface will be there. 

To allow it to work with the rest of the program, add `"events_rest_api"` and `"map_events"` to `events` in the config file. 

When you visit the web interface, you'll be prompted to login. The default password is `this is quite the default password`. The password can be changed by going to `Config > Change Password`


# Configuration

You can edit the `config.json` file or make a new config file and run the program with `--config=filename.json` to select that new config file when running.



## API Keys
You can set API keys in the `keys.json` file, or use a different file and add `--keys=filename.json` when running to select a different keys file.

To use google maps API, you'll need to supply an api key to "gmaps" in the config. Otherwise, it'll do its best to use other options for geocoding addresses.

For push notifications, you'll need pushover. Set the "pushover_token" and "pushover_user" to the application token and user token for your pushover account.


## Filters
You can create allow-lists and block-lists for each location to filter by incident type. This can be easily done through the web interface by going to `Edit Locations > Edit Location` for the location you want to configure. 
Incident types can be found under `/dev/core/incident_types.json`.

## For those in Portland who want to monitor police activity
Add `"police_incidents"` to `events` in the config file. Police activity in portland will be monitored via scraping twitter. You'll also need a twitter bearer token, put that into the `keys.json` file under `twitterbearertoken`.


# PPDB

PulsePoint DB is a "sub project" where instead of monitoring specific locations, I monitor every single agency, scanning each one every twelve hours. It doesn't scan and scrape from them all at once, instead it generates a schedule so that its API calls are distributed evenly throughout each day. After scanning an agency, it collects all the information about each incident and inserts it into a MongoDB database collection. 

To use the program, create a mongoDB database called "pulsepoint", and then run 
`python3 -m dev.ppdb`

Additional configuration options are available in `dbconfig.json`

