PeopleMapController = function () { }

PeopleMapController.prototype.initialize = function(options) {
    this.person_locations = {};

    var number_of_people_geocoded = 0;
    var update_all_markers;

    var person_id2data = options['person_id2data'];
    this.get_person_id2data = function() { return person_id2data; };
    var num_of_persons_with_locations = options['num_of_persons_with_locations'];

    var all_markers = [];

    var geocoder =  new google.maps.Geocoder();

    this.mapOrigin = new google.maps.LatLng(0, 0);
    var myOptions = {
        'zoom': 1,
        'center': this.mapOrigin,
        'mapTypeId': google.maps.MapTypeId.ROADMAP
    };

    var $canvas = $('#map_canvas');

    // This allows you to access the map globally, on this object
    this.map = new google.maps.Map($canvas.get(0), myOptions);

    // Hide the background image after 2.5 seconds.
    var hideBGImage = function () { $canvas.css('background-image', ''); };
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
        var data = person_id2data[person_id];
        var location_name = data['location'];
        var name = data['name'];

        function create_a_callback(mapController, person_name, person_id) {

            // As specified after the "create_a_callback" function,
            // the following callback will be executed when the
            // Google Maps API responds to our request for geographic data.
            return function(results, status) {
                number_of_people_geocoded += 1;
                var person_location = results[0].geometry.location;

                if (status == google.maps.GeocoderStatus.OK) {
                    var marker = new google.maps.Marker({
                        'map': mapController.map, 
                        'title': person_name,
                        'person_id': person_id,
                        'position': person_location
                    });
                    mapController.person_locations['' + person_id] = person_location;
                    mapController.map.setCenter(mapController.mapOrigin);
                    google.maps.event.addListener(marker,
                            'click', function() {
                            mapController.highlightPerson(marker.person_id);
                            });
                    all_markers.push(marker);
                }
                else {
                    console.log("Geocode was not successful for the following reason: " + status);
                }
                /* if this is the last one, call update_all_markers() */
                if (num_of_persons_with_locations == number_of_people_geocoded) {
                    update_all_markers();
                }
            }
        }

        // Ask the Google Maps API for some geographic data, concerning a particular
        // location.
        geocoder.geocode( { 'address': location_name},
                create_a_callback(this, name, person_id));
    }

    function generate_update_all_markers(map) {
        return function() {
            /* This only makes up to 10 people show on the right. */
            var MAX_TO_SHOW = 10;
            var shown_this_many = 0;

            for (var i = 0; i < all_markers.length; i++) {
                var marker = all_markers[i];
                var $person_bullet = $('#person_bullet_' + marker.person_id);
                if (map.getBounds().contains(marker.position) && 
                        shown_this_many < MAX_TO_SHOW) {

                    // If the person bullet is hidden, display it at the bottom of the list.
                    if($person_bullet.is(':visible') === false) {
                        console.log($person_bullet.get(0).id);
                        $person_bullet.appendTo('#people-list');
                        $person_bullet.show();
                    }
                    shown_this_many += 1;
                }
                else {
                    $person_bullet.hide();
                } 
            }
            var people_shown_string = "" 
            if(shown_this_many == 1){
                people_shown_string = "1 person in this area:" ;
            }
            else if(shown_this_many == 0){
                people_shown_string = "Nobody in this area.";
            }
            else if(shown_this_many == num_of_persons_with_locations){
                people_shown_string = num_of_persons_with_locations + " people have entered their location:";
            }
            else{
                people_shown_string = shown_this_many + " people in this area:" ;

            }
            $('#people-count').text(people_shown_string);
        }
    }
    update_all_markers = generate_update_all_markers(this.map);
    google.maps.event.addListener(this.map,
            'idle',
            update_all_markers);
    google.maps.event.addListener(this.map,
            'bound_changed',
            update_all_markers);
}

//this gets called when you click a marker on the map
PeopleMapController.prototype.highlightPerson = function(personId) {
    // Unhighlight everyone
    $('#people-list li').removeClass("highlighted");
    //highlight the right person
    $('#person_bullet_' + personId).addClass("highlighted");
}


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

    };
    $('#people-list li').click(handler);
    $('#people-list li').hoverClass('hover');
}
