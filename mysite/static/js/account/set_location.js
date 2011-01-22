/*
# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2010 OpenHatch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

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
