// Depends on jQuery.

var makeNewInput = function() {
    var $form = $('.queries form');
    html = "<input type='text' name='NAME' id='NAME' />";
    html = html.replace(/NAME/g, 
            "commit_username_" + $form.find('input').size());
    $new_input = $(html).appendTo($form);
}
var keyupHandler = function() {
    $input = $(this);
    var oneInputIsBlank = function() {
        var ret = false;
        $('.queries form input').each(function () {
                var thisInputIsBlank = (
                    $(this).val().replace(/\s/g,'') == '' );
                if (thisInputIsBlank) ret = true;
                });
        return ret;
    }();
    if (!oneInputIsBlank) {
        makeNewInput();
        bindKeyupHandlers();
    }
}
var bindKeyupHandlers = function() {
    var $form = $('.queries form');
    $form.children('input').keyup(keyupHandler);
}
$(bindKeyupHandlers);

var submitDataSources = function() {
    $checkboxes = $(".data_import_attempts input[type='checkbox']:checked");
    checkboxIDs = [];
    $checkboxes.each(function () {
        $cb = $(this);
        checkboxIDs.push($cb.attr('id'));
    });

    // Post
    var url = "/people/user_selected_these_dia_checkboxes";
    var callback = function(response) {
        if (response == '0') {
            alert('Oops. An error occurred while trying ' +
                    'to import your data. Please reload the page.');
        } else {
            enableThrobbersThenPollForStatusForever();
        }
    };
    var data = {'checkboxIDs': checkboxIDs.join(" ")};
    console.debug(data);
    $.post(url, data, callback);
}
$.fn.setThrobberStatus = function(theStatus) {
    $cb = this;
    var $throbber = $cb.parent().find(
            '.data_import_status img');
    console.debug("Trying to set status of throbber: ", $throbber.get(0));
    $throbber.css('visibility', 'visible');
    mapStatusToImage = {
        'working': '/static/images/throbber.gif',
        'succeeded': '/static/images/icons/finished-successfully.png',
        'failed': '/static/images/icons/finished-unsuccessfully.png',
    }
    src = mapStatusToImage[theStatus];
    if ($throbber.attr('src') != src) {
        $throbber.attr('src', src);
    }
    console.debug($throbber.get(0));
}
var enableThrobbersThenPollForStatusForever = function() {
    var $checkboxes = $(".data_import_attempts input[type='checkbox']:checked");
    // Enable throbbers.
    $checkboxes.each(function () {
            $cb = $(this);
            $cb.setThrobberStatus('working');
            });

    // Ask server for a list of dias, which will tell us
    // which importation background jobs have finished,
    // and if they finished successfully.
    var are_they_done_url = "/people/gimme_json_that_says_that_commit_importer_is_done";
    var allDone = undefined;
    var ask_if_done = function () {
        console.log('Asking if done yet.');
        var callback = function(dias) {
            var allSeemsDone = true;
            console.log(dias);
            for (var d = 0; d < dias.length; d++) {
                var dia = dias[d];
                console.debug("while polling for status, server returned this dia", dia);
                var $checkbox = $("#data_import_attempt_" + dia.pk);
                console.debug("while polling for status, attempted to set status of throbber for checkbox: ", $checkbox.get(0));
                var diaStatus = null;
                if (dia.fields.completed) {
                    diaStatus = dia.fields.failed ? "failed" : "succeeded";
                }
                else {
                    diaStatus = 'working';
                }
                if ($checkbox.is(':checked')) {
                    $checkbox.setThrobberStatus(diaStatus);
                }
                if (diaStatus == 'working') {
                    allSeemsDone = false;
                }
            }
            allDone = allSeemsDone;
        };
        $.getJSON(are_they_done_url, callback);

        // Stop asking when all the data imports have finished,
        // successfully or not.
        if (allDone) {
            console.log('All the jobs have finished!');
            window.clearInterval(window.askIfDoneInterval);
        }
    }
    window.askIfDoneInterval = window.setInterval(ask_if_done, 1000);
}
var bindSubmitButtonClickHandler = function() {
    $('#submit_data_sources').click(submitDataSources);
}
$(bindSubmitButtonClickHandler);
