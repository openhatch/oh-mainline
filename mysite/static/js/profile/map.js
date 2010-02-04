PeopleMapController = function () { };

PeopleMapController.prototype.geocode = function(data, callback) {
    var ajaxOptions = {
	'url': '/+geocode',
	'type': 'GET',
	'data': data,
	'dataType': 'json',
	'success': function(data) {
	    callback(data, true);
	    },
	'error': function() {
	    callback(null, false);
	    }
    };
    $.ajax(ajaxOptions);
};


PeopleMapController.prototype.initialize = function(options) {
    this.person_locations = {};

    var number_of_people_geocoded = 0;
    this.get_number_of_people_geocoded = function() { return number_of_people_geocoded; };
    var update_all_markers;

    var person_id2data = options['person_id2data'];
    this.get_person_id2data = function() { return person_id2data; };
    
    //these two might not be the same because we store location strings even if we can't geocode them
    var num_of_persons_with_locations_in_db = options['num_of_persons_with_locations'];
    var num_of_persons_who_can_be_geocoded = num_of_persons_with_locations_in_db;

    var all_markers = [];

    this.mapOrigin = new google.maps.LatLng(options.center.latitude,
					    options.center.longitude);
    var myOptions = {
        'zoom': options.center.suggested_zoom_level,
        'center': this.mapOrigin,
        'mapTypeId': google.maps.MapTypeId.ROADMAP
    };

    var $canvas = $('#map_canvas');

    // This allows you to access the map globally, on this object
    this.map = new google.maps.Map($canvas.get(0), myOptions);

    // Hide the background image after 2.5 seconds.
    var hideBGImage = function () { $canvas.css('background', ''); };
    window.setTimeout(hideBGImage, 2500);

    /*
     * This function is called with an option named "person_id2data".
     * This is a JS object (sort of like a Python dictionary)
     * mapping the primary keys of Django-side Person objects to
     * a JS object containing information about that person.
     *
     * (We smuggled the Python data into JavaScript by having Python
     * write a certain bit of JavaScript that defines a JS object.
     * That all happens in a piece of inline JS, in the template
     * located at profile/templates/profile/map.html .)
     */
    for (var person_id in person_id2data) {
        console.log(person_id2data.length);
        var data = person_id2data[person_id];
        var location_name = data['location'];
        var name = data['name'];

        function create_a_callback(mapController, person_name, person_id) {

            // As specified after the "create_a_callback" function,
            // the following callback will be executed when the
            // Google Maps API responds to our request for geographic data.
            return function(json_data, it_worked) {
                number_of_people_geocoded += 1;

		if (! it_worked) {
		    console.log('boom');
		    num_of_persons_who_can_be_geocoded -=1;
		    return;
		}
		console.log('onwards');
		console.log(json_data);
		var person_location = new google.maps.LatLng(json_data['latitude'],
							     json_data['longitude']);
		
                var marker = new google.maps.Marker(
		    {
                        'map': mapController.map, 
                        'title': person_name,
                        'person_id': person_id,     
                        'position': person_location
                    });
                mapController.person_locations['' + person_id] = person_location;
                mapController.map.setCenter(mapController.mapOrigin);
                google.maps.event.addListener(
		    marker,
		    'click', function() {
			mapController.highlightPerson(marker.person_id);
                        window.location.hash=('person_summary_' + marker.person_id);
                    });
                all_markers.push(marker);
                /* if this is the last one, call update_all_markers() */
                if (num_of_persons_who_can_be_geocoded == number_of_people_geocoded) {
                    update_all_markers();
                    google.maps.event.addListener(mapController.map,
                            'idle',
                            update_all_markers);
                }
            };
        }

        // Ask the OpenHatch Geocoder API ;-) for some geographic data, concerning a particular
        // location.
        this.geocode( { 'address': location_name},
                create_a_callback(this, name, person_id));
    } // end for loop

    function update_people_count() {
        alert('yo');
        //when you can see everyone, this text should be different
        var people_shown_string = "" ;
        var mappedPeople_count = $("#people-list li:visible").size();

        var str = mappedPeople_count;
        console.log('mappedPeople_count', mappedPeople_count);
        if (mappedPeople_count == num_of_persons_who_can_be_geocoded) {
            str = "Everybody";
            $('#how_many_people_are_visible_label').hide();
            $('#how_many_people_are_visible').text(mappedPeople_count);
            return;
        }
        if (mappedPeople_count == 0) {
            str = "Nobody";
        }
        $('#how_many_people_are_visible_label').show();
        $('#how_many_people_are_visible').text(mappedPeople_count);
    } // end function update_people_count

    function generate_update_all_markers(map) {
        return function() {
            /* This only makes up to 10 people show on the right. */
            var shown_this_many = 0;

            for (var i = 0; i < all_markers.length; i++) {
                var marker = all_markers[i];
                var $person_summary = $('#person_summary_' + marker.person_id);
                if (map.getBounds().contains(marker.position)) {

                    // If the person bullet is hidden,
                    if($person_summary.is(':visible') === false) {

                        $person_summary.show();
                    }
                    shown_this_many += 1;
                }
                else {
                    $person_summary.hide();
                } 
            }
            update_people_count();
        };
    } // end function generate_update_all_markers

    update_all_markers = generate_update_all_markers(this.map);
    google.maps.event.addListener(this.map,
            'bound_changed',
            update_all_markers);
};

//this gets called when you click a marker on the map
PeopleMapController.prototype.highlightPerson = function(personId) {
    // Unhighlight everyone
    $('#people-list li').removeClass("highlighted");
    //highlight the right person
    $('#person_summary_' + personId).addClass("highlighted");
};


//binds the clickhandlers to people list items
PeopleMapController.prototype.bindClickHandlersToPeopleListItems = function() {
    //grab google's map object
    var me = this;
    //grab list of person locations
    //var person_locations = this.person_locations;
    //click handler for people list items
    handler = function(event) {
        thePersonLi = this;

        // Unhighlight everyone
        $('#people-list li').removeClass("highlighted");

        // Highlight this person.
        $(thePersonLi).addClass("highlighted");

        //grab the person's database id from her dom id
        var thePersonId = thePersonLi.id.split("_")[2];

        // Center the map on it
        me.map.setCenter(me.person_locations[thePersonId]);
        
        // Center the map on their marker.

    }; // end function "handler"
    $('#people-list li').click(handler);
    $('#people-list li').hoverClass('hover');
};
