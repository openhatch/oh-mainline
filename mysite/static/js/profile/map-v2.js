function drawAllPeopleDivsAtOnce(list_of_people_data) {
    var MAX_TO_DISPLAY = 100;
    var $text = $("<div>Drawing people...</div>");
    var i;
    var f;
    var div;
    var a;
    var span;
    var $results = $('<div id="results"></div>');

    $("#results").replaceWith($text);


    for (i = 0; i < list_of_people_data.length && i < MAX_TO_DISPLAY; i++) {
	f = list_of_people_data[i];
        div = $("<div />");
        a = $("<a class='person' href='http://openhatch.org/people/"+f.attributes.all_data.extra_person_info.username+"/'>" + f.attributes.name + "</a>");
        div.append(a);
        span = $("<span class='geocode'>, " + f.attributes.location + "</span>");
        div.append(span);
        $results.append(div);
    }
    if (list_of_people_data.length >= MAX_TO_DISPLAY) {
	$results.append($("<div>and " + (list_of_people_data.length - MAX_TO_DISPLAY) + " more; zoom the map to see them, or search for them specifically.</div>"));
    }

    $text.replaceWith($results);
}

function drawResults() {
    var people_to_display_now = [];
    var extent = map.getExtent();
    var i;
    var feat;
    var j;
    var f;

    for (i = 0; i < layer.features.length; i++) {
        feat = layer.features[i];
        if (extent.intersectsBounds(feat.geometry.getBounds()))  {
            for (j = 0 ; j < feat.cluster.length; j++) {
                f = feat.cluster[j];
		people_to_display_now.push(f);
	    }
	}
    }
    drawAllPeopleDivsAtOnce(people_to_display_now);
}

function handleResults(data) {
    var key;
    var features = [];
    var person;
    var feature;

    for (key in data) {
	if (data.hasOwnProperty(key)) {
            person = data[key];
            feature = new OpenLayers.Feature.Vector(new OpenLayers.Geometry.Point(
		person.lat_long_data.longitude,
		person.lat_long_data.latitude),
						    {'name':person.name, 'location': person.location, 'all_data': person});
            feature.geometry.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
            features.push(feature);
	}
    }
    layer.destroyFeatures();
    layer.addFeatures(features);
    drawResults();
}

function init() {
    map = new OpenLayers.Map("map_canvas");
    var l = new OpenLayers.Layer.OSM();
    l.transitionEffect = "resize";
    map.addLayer(l);
    var styleMap =new OpenLayers.StyleMap({'default': new OpenLayers.Style(
        { fillColor: 'red','pointRadius':'${radius}', 'label': "${label}" },
                {
                    context: {
                        label: function(feature) {
                            return feature.cluster.length;
                        },
                        radius: function(feature) {
                            return feature.cluster ?
                                Math.min((Math.max(feature.cluster.length, 7) + 8)/2, 16) :
                                15;
                        }
                    }
                })});

    var s = new OpenLayers.Strategy.Cluster();
    layer = new OpenLayers.Layer.Vector("", {strategies: [ s ], styleMap: styleMap});
    map.addLayer(layer);
    s.activate();
    map.setCenter(new OpenLayers.LonLat(0, 0), 1);
    var query_string = 'person_ids=' + person_ids;
    jQuery.getJSON("/+profile_api/location_data/?" + query_string, handleResults);
    map.events.register("moveend", null, drawResults);
}
