PeopleMapController = function () { }

PeopleMapController.prototype.initialize = function(options) {
    var me = this;
    this.person_locations = {};

    var number_of_people_geocoded = 0;
    var update_all_markers;

    var person_id2data = options['person_id2data'];
    var num_of_persons_with_locations = options['num_of_persons_with_locations'];

    var all_markers = [];

    var geocoder =  new google.maps.Geocoder();

    var latlng = new google.maps.LatLng(0, 0);
    var myOptions = {
        'zoom': 1,
        'center': latlng,
        'mapTypeId': google.maps.MapTypeId.ROADMAP
    };
    var $canvas = $('#map_canvas');
    //this allows you to access the map globally, on this object
    this.map = new google.maps.Map($canvas.get(0), myOptions);


    var hideBGImage = function () { $canvas.css('background-image', ''); }
    window.setTimeout(hideBGImage, 2500);

    for (var person_id in person_id2data) {
        var data = person_id2data[person_id];
        var location_name = data['location'];
        var name = data['name'];

        function create_a_callback(person_name, person_id) {
            return function(results, status) {
                number_of_people_geocoded += 1;
                var person_location = results[0].geometry.location;
                if (status == google.maps.GeocoderStatus.OK) {
                    var marker = new google.maps.Marker({
                        'map': me.map, 
                        'title': person_name,
                        'person_id': person_id,
                        'position': person_location
                    });
                    me.person_locations[person_id] = person_location;
                    google.maps.event.addListener(marker,
                            'click', function() { me.highlightPerson(marker.person_id); });
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

        geocoder.geocode( { 'address': location_name}, create_a_callback(name, person_id));
    }

    function generate_update_all_markers(map) {
        return function() {
            /* This only makes up to 10 people show on the right. */
            var MAX_TO_SHOW = 10;
            var shown_this_many = 0;

            for (var i = 0; i < all_markers.length; i++) {
                var marker = all_markers[i];
                var $person_bullet = $('#person_bullet_' + marker.person_id);
                console.debug(map);
                if (map.getBounds().contains(marker.position) && 
                        shown_this_many < MAX_TO_SHOW) {
                    $person_bullet.show();
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
    var map = this.map;
    //grab list of person locations
    var person_locations = this.person_locations;
    //click handler for people list items
    handler = function(event) {
        thePersonLi = this;

        // Unhighlight everyone
        $('#people-list li').removeClass("highlighted");

        // Highlight this person.
        $(thePersonLi).addClass("highlighted");

        console.debug(map);
        //grab the person's database id from her dom id
        var thePersonId = thePersonLi.id.split("_")[2];
        // Center the map on it
        map.setCenter(person_locations[thePersonId]);


        
        // Center the map on their marker.

    };
    $('#people-list li').click(handler);
}
