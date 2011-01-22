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

function addHandlersToLocationDialogLinks(){
    $("#location_confirm_suggestion").click(locationConfirmSuggestionHandler);
    function reload_if_location_page(){
        if(document.location.pathname == '/account/settings/location/'){
           window.location.reload(); 
        }
    }
    var confirmOptions = {
        'url': "/account/settings/location/confirm_suggestion/do",
        'success': function() {
            $("#location-suggestion-notification").html('Thank you! Check yourself out on the <strong><a href="/people/">Map of People</a></strong>. You can change your location at any time by clicking <a href="/account/settings/location/">Location</a> in your <a href="/account/settings/">Settings</a>.');
            //if your location is the location page, reload this page
            reload_if_location_page()
        },
        'error': function() { },
        'type': "POST",
    };
    function locationConfirmSuggestionHandler() {
        $.ajax(confirmOptions);
        return false;
    }

    $("#location_dont_track").click(locationDontTrackHandler);
    var dontTrackOptions = {
        'url': "/account/settings/location/dont_guess_location/do",
        'success': function() {
            $("#location-suggestion-notification").html('You got it! You can set your location at any time by clicking <a href="/account/settings/location/">Location</a> in your <a href="/account/settings/">Settings</a>.');
            //if your location is the location page, reload this page
            reload_if_location_page()
        },
        'error': function() { },
        'type': "POST",
    };
    function locationDontTrackHandler() {
        $.ajax(dontTrackOptions);
        return false;
    }
}
$(addHandlersToLocationDialogLinks);
