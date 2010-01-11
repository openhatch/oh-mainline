/* initialize() gets called on DOM ready.
 * 
 * It geocodes the last-saved location for this person, then creates
 * a map to show where that geocodes to.
 *
 * If it fails to geocode, ...?
 */
function initialize() {
    // grab location on DOM ready
    var location_name = $('#id_edit_location-location_display_name').val();

    var thing_to_call_once_geocode_happens = function(results, status) {
        if (status == google.maps.GeocoderStatus.OK) {
            var myOptions = {
                'zoom': 6,
                'center': results[0].geometry.location,
                'mapTypeId': google.maps.MapTypeId.ROADMAP
            };
            var map = new google.maps.Map(document.getElementById("map_canvas"), 
                    myOptions);
            var marker = new google.maps.Marker({
                    'map': map, 
                    'title': 'You',
                    'position': results[0].geometry.location
                    });
            $('#geocode_description').css('visibility', 'visible');
            $('#success_message').css('visibility', 'visible');
        }
        else {
            $('#map_canvas').text("Could not find coordinates for that location. Try being more specific.");
        }
    };

    if (location_name == ''){
        $('#map_canvas').remove();

    }
    else {
        var geocoder =  new google.maps.Geocoder();
        geocoder.geocode( { 'address': location_name},
                thing_to_call_once_geocode_happens);
    }
}
