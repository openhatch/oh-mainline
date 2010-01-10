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
            $("#location-suggestion-notification").html('Thank you! Check yourself out on the <a href="/people/">Map!</a> You can change your location at any time by clicking <a href="/account/settings/location/">Location</a> in your <a href="/account/settings/">Settings</a>.');
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
