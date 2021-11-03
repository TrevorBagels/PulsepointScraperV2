Eventually, PulsepointScraper will have an interface that can be used to do things like adjust the config, view incidents, etc. Actually, many months ago I tried to implement such a dashboard, and at some point I abandoned it because it felt like too much work. The dashboard I created allowed you to view the logs, add new locations (and automatically add agencies based on the coords of those locations), adjust config settings, and more.



Instead of using flask for the interface and everything, I'll make the interface a seperate project, and focus on making some API for javascript to retreive and send info with.