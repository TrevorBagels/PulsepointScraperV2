var MAP;
var mapIcons = {};
var mapIconNames = {};
var mapCluster;
var heatLayer;
var heatPoints = [];
var incidentPoints = []; // a list of incidents
var mapTileLayer;
var mapCfg;

var mapTileLayerIndex = Cookies.get("mapindex") || 0;
function createIcon(icon, color, name){
	mapIcons[name] = L.AwesomeMarkers.icon({"extraClasses": "fa-rotate-0", "icon": icon, "iconColor": "white", "markerColor": color, "prefix": "fa"});
}
function changeTileLayer()
{
	mapTileLayerIndex += 1;
	if(mapTileLayerIndex > 2)
	mapTileLayerIndex = 0;
	Cookies.set("mapindex", mapTileLayerIndex)
	tiles = [mapCfg.tiles, mapCfg.tiles2, mapCfg.tiles3];
	url = tiles[mapTileLayerIndex];
	try {
		mapTileLayer.setUrl(url);
	}
	catch{
		
	}
}
function setMapToCorrectTiles()
{	
	tiles = [mapCfg.tiles, mapCfg.tiles2, mapCfg.tiles3];
	url = tiles[mapTileLayerIndex];
	mapTileLayer.setUrl(url);
}
function setupMap(callback){
	//set up icons
	$.get(baseURL + "/mapicons", {token: Cookies.get("auth")}, function (icons){
		mapIconNames = icons
		Object.keys(icons).forEach(function(e){
			i = icons[e]
			icon = i.split("|")[0]
			color = i.split("|")[1]
			createIcon(icon, color, e);
			createIcon(icon, "lightgray", "OLD_"+e);
		});
		//set up map
		$.get(baseURL + "/settings", {token: Cookies.get("auth")}, function(config){
			var cfg = config.map_config
			var center = config.locations[0].coords || [0, 0]
			var zoomstart = cfg.zoom_start
			MAP =  L.map("MAP")
			var tiles = cfg.tiles
			mapCfg = cfg
			MAP.setView(center, zoomstart)
			mapTileLayer = L.tileLayer(tiles,
			{"attribution": "...", "detectRetina": false, 
			"maxNativeZoom": 20, "maxZoom": 20, "minZoom": 0, 
			"noWrap": false, "opacity": 1, "subdomains": "abc", "tms": false})
			mapTileLayer.addTo(MAP);
			mapCluster	 = L.markerClusterGroup({"animate": true, "maxClusterRadius": cfg.max_cluster_radius, 
			"spiderLegPolylineOptions": {"color": "#00f", "opacity": 1, "weight": 3}, 
			"spiderfyOnMaxZoom": true});
			MAP.addLayer(mapCluster);
			if(cfg.thermal_enabled)
			{
				heatLayer = L.heatLayer([], {"blur": cfg.thermal_blur, "maxZoom": cfg.thermal_max_zoom, "minOpacity": cfg.thermal_min_opacity, "radius": cfg.thermal_radius});
				heatLayer.addTo(MAP);
			}
			//initiate the callback
			MAP.setZoom(12);
			setMapToCorrectTiles();
			/*
			t1 = document.createElement('div')
			t1.id = 'mapoverlaycontainer'
			var t = document.createElement('span')
			t.id = "mapoverlay"
			//t.src = "https://art.pixilart.com/0928a2aa14e88da.gif"//https://thumbs.gfycat.com/FittingBowedAnemone-size_restricted.gif"
			t1.appendChild(t)
			document.getElementById("MAP").appendChild(t1)*/
			callback(config);
		});

	});
	

}




function addMarker(location, tooltip, popup, icon_name, target, heat, lineTo, old){
	o = ""
	if(old) o = "OLD_"
	var m = L.marker(location, {}).bindPopup(popup).bindTooltip(tooltip).setIcon(mapIcons[o + icon_name])
	if(target == "markercluster")
		m.addTo(mapCluster);
	else
		m.addTo(MAP)
	if(heat && heatLayer != null)
		heatLayer.addLatLng(location);
	if(lineTo != null)
	{
		c = mapIconNames[icon_name].split("|")[1]
		speed =  (1-(MAP.distance(lineTo, location) / mapCfg.minimum_line_distance)) * 30 + 15
		L.polyline([lineTo, location], {"bubblingMouseEvents": true, "color": c, "dashArray": mapCfg.line_dash,
			"dashOffset": null, "dashSpeed": speed, "fill": false, "fillColor": c, "fillOpacity": 0.2,
			"fillRule": "evenodd", "lineCap": "round", "lineJoin": "round", "noClip": false,
			"opacity": mapCfg.lineOpacity, "smoothFactor": 1.0, "stroke": true, "weight": 1.5}).addTo(mapCluster)
	}
}






//addMarker([45.2, -122.12], "tooltip", "text for popup", "Traffic Collision", "map", false)
//addMarker([45.251041, -122.694986], "tooltip", "text for popup", "Traffic Collision", "markercluster", true)
//addMarker([45.25111, -122.6946], "tooltip", "text for popup", "Traffic Collision", "markercluster", true)
//addMarker([45.299355, -122.65877], "tooltip", "text for popup", "Traffic Collision", "markercluster", true, [45.251041, -122.694986])
//updateHeat()





L.Control.MousePosition = L.Control.extend({
	options: {
	  position: 'bottomleft',
	  separator: ' : ',
	  emptyString: 'Unavailable',
	  lngFirst: false,
	  numDigits: 5,
	  lngFormatter: undefined,
	  latFormatter: undefined,
	  prefix: ""
	},
  
	onAdd: function (map) {
	  this._container = L.DomUtil.create('div', 'leaflet-control-mouseposition');
	  L.DomEvent.disableClickPropagation(this._container);
	  map.on('mousemove', this._onMouseMove, this);
	  this._container.innerHTML=this.options.emptyString;
	  return this._container;
	},
  
	onRemove: function (map) {
	  map.off('mousemove', this._onMouseMove)
	},
  
	_onMouseMove: function (e) {
	  var lng = this.options.lngFormatter ? this.options.lngFormatter(e.latlng.lng) : L.Util.formatNum(e.latlng.lng, this.options.numDigits);
	  var lat = this.options.latFormatter ? this.options.latFormatter(e.latlng.lat) : L.Util.formatNum(e.latlng.lat, this.options.numDigits);
	  var value = this.options.lngFirst ? lng + this.options.separator + lat : lat + this.options.separator + lng;
	  var prefixAndValue = this.options.prefix + ' ' + value;
	  this._container.innerHTML = prefixAndValue;
	}
  
  });
  
  L.Map.mergeOptions({
	  positionControl: false
  });
  
  L.Map.addInitHook(function () {
	  if (this.options.positionControl) {
		  this.positionControl = new L.Control.MousePosition();
		  this.addControl(this.positionControl);
	  }
  });
  
  L.control.mousePosition = function (options) {
	  return new L.Control.MousePosition(options);
  };

/*
var mapCoords;
function toggleShowCoords()
{
	value = Number(Cookies.get("showcoords"));
	if(value == undefined){
		value = 0;
	}
	value = !value
	if(!value) {
		document.getElementById("coordDisplay").innerHTML = "";
		MAP.removeEventListener(mapCoords);
		mapCoords = null;
	}
	Cookies.set("showcoords", Number(value));
	document.getElementsByClassName("leaflet-popup-close-button")[0].click();
}

function addCoordsToMap(){
	if(mapCoords != null)
		return;
	mapCoords = document.getElementById("MAP").addEventListener("mousemove", e => {
		var d = document.getElementById("coordDisplay");
		d.style.top = (e.y + 45) + "px";
		d.style.left = (e.x - 25) + "px";
		latlng = MAP.mouseEventToLatLng(e);
		rnd = 4;
		d.innerHTML = math.round(latlng.lat, rnd) + " " + math.round(latlng.lng, rnd);
	});
}

if(Number(Cookies.get("showcoords")))
{
	addCoordsToMap();
}
*/