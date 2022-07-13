# PulsepointScraperV2
Scrapes pulsepoint.org for emergency incidents and notifies you if certain conditions are met.

<img src="https://user-images.githubusercontent.com/61929192/178640227-faa5ef1b-12c8-4e05-8895-8d896de9ddfe.png"/>

<img src="https://user-images.githubusercontent.com/61929192/178640290-161d199c-4bc8-405a-a73d-3f823fd9b2f1.png"/>

<div style='width: 100%;'>
<img style='float:left' src="https://user-images.githubusercontent.com/61929192/178640485-6006b081-4231-4829-857b-87deb702cf45.png" width="600"/>

<img style='float:right; margin-right: 0;' src="https://user-images.githubusercontent.com/61929192/178640525-5284fae7-122a-4fae-bd61-baf35362b755.png" alt="mobile notifications" width="200"/>
</div>
<img src="https://user-images.githubusercontent.com/61929192/178641366-da85e47b-ac83-40e0-adcf-d1c94bbe1abf.png"/>
<img src="https://user-images.githubusercontent.com/61929192/178641277-4948449d-edd8-409c-90c6-793c0bc8b0c4.png"/>

# Setting up Pulsepoint Monitor with web interface

1. Clone the repository (V3 branch) `git clone --branch V3 https://github.com/TrevorBagels/PulsepointScraperV2.git`
2. Navigate to the new directory `cd PulsepointScraperV2`
3. Install requirements `pip3 install -r requirements.txt`
4. Run `python3 -m dev`

# Web interface
To enable the web app, you'll need to use <a href="https://jekyllrb.com/">Jekyll</a>. If you have Jekyll installed, you should be able to run the web interface by running `bundle exec jekyll serve -H 0.0.0.0` from the `/site` directory after running `bundle install` in the same directory. 

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

