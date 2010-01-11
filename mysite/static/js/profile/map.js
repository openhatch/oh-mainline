PeopleMap = function () { }

PeopleMap.prototype.initialize = function(options) {

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
    var map = new google.maps.Map($canvas.get(0), myOptions);

    var hideBGImage = function () { $canvas.css('background-image', ''); }
    window.setTimeout(hideBGImage, 2500);

    for (var person_id in person_id2data) {
        var data = person_id2data[person_id];
        var location_name = data['location'];
        var name = data['name'];

        function create_a_callback(person_name, person_id) {
            return function(results, status) {
                number_of_people_geocoded += 1;
                if (status == google.maps.GeocoderStatus.OK) {
                    var marker = new google.maps.Marker({
                            'map': map, 
                            'title': person_name,
                            'person_id': person_id,
                            'position': results[0].geometry.location
                    });
                    /*google.maps.event.addListener(marker,
                     'click', function() { 	alert('hi'); }); */
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
                if (map.getBounds().contains(marker.position) && 
                        shown_this_many < MAX_TO_SHOW) {
                    $person_bullet.show();
                    shown_this_many += 1;
                }
                else {
                    $person_bullet.hide();
                }
            }
        }
    }
    update_all_markers = generate_update_all_markers(map);
    google.maps.event.addListener(map,
            'idle',
            update_all_markers);
    google.maps.event.addListener(map,
            'bound_changed',
            update_all_markers);
}
