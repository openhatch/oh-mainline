// Depends on jQuery.

var askServerToBeginQuerying = function () {
    console.log('Query add');
}

var getStrings = function(schema, dictionaries) {
    /* Returns an array of strings.
     * Each string is the result of the string `schema'
     * translated according to the mappings
     * provided by a dictionary in `dictionaries'.
     *
     * <example>
     * <input>
     *
     *  var schema = "In $LANGUAGE, hello is '$HELLO', "
     *      + "goodbye is '$GOODBYE', thank you is '$THANKYOU'";
     *
     *  var french = {
     *      '$LANGUAGE': 'French',
     *      '$HELLO': 'Salut',
     *      '$GOODBYE': "A tout à l'heure",
     *      '$THANKYOU' 'Merci beaucoup'
     *      };
     *
     *  var turkish = {
     *      '$LANGUAGE': 'Turkish',
     *      '$HELLO': 'Merhaba',
     *      '$GOODBYE': 'Hoscakal',
     *      '$THANKYOU' 'Tesekkurler'
     *      };
     *
     *  var yiddish = {
     *      '$LANGUAGE': 'Yiddish',
     *      '$HELLO': 'Sholem aleykham',
     *      '$GOODBYE': 'Zay gesunt',
     *      '$THANKYOU' 'A sheynem dank'
     *      };
     *
     *  var dictionaries = [french, turkish, yiddish];
     *
     *  applyDictionariesToSchema(dictionaries, schema);
     *
     * </input>
     *
     * <output>
     * // Array of strings.
     * [
     *      "In French, hello is 'Salut', goodbye is 'A tout à l'heure', thank you is 'Merci beaucoup'",
     *      "In Turkish... etc.",
     *      "In Yiddish... etc."
     *      ]
     *
     * </output>
     * </example>
     */
    var strings = [];
    for (var d = 0; d < dictionaries.length; d++) {
        var dictionary = dictionaries[d];
        var str = schema;
        for (var mapFrom in dictionary) {
            var mapTo = dictionary[mapFrom];
            mapFromRegExp = new RegExp(mapFrom.replace("$", "\\$"), "g");
            str = str.replace(mapFromRegExp, mapTo);
        }
        strings.push(str);
    }
    return strings;
};

var makeNewInput = function() {
    var $table = $('.input table');
    var index = $('.input .query').size();
    var html = ""
        + "<div id='query_$INDEX' class='query'>"
        + "   <div class='username'>"
        + "       <input type='text' />"
        + "   </div>"
        + "   <ul class='data_sources'>"

    var sourceDictionaries = [
        {'$ID': 'rs', '$DISPLAY': 'All repositories'},
        {'$ID': 'lp', '$DISPLAY': "<img src='/static/images/icons/data-sources/launchpad.png' alt='Launchpad' />"},
        {'$ID': 'ou', '$DISPLAY': "<img src='/static/images/icons/data-sources/ohloh.png' alt='Ohloh' />"},
    ];

    var checkboxTDSchema = ""
        + "       <li class='data_source selected'>"
        + "            <input type='checkbox' checked "
        + "                name='checkbox_$INDEX_$ID' "
        + "                id='checkbox_$INDEX_$ID' />"
        + "            <label for='checkbox_$INDEX_$ID'>"
        + "                $DISPLAY"
        + "            </label>"
        + "       </li>";

    html += getStrings(checkboxTDSchema, sourceDictionaries).join("\n")
        + "    </ul>"
        + "</div>";

    html = html.replace(/\$INDEX/g, index);

    $(html).appendTo($table);

    bindHandlers();
};

var keydownHandler = function() {
    console.log('keydown!');
    $input = $(this);
    var oneInputIsBlank = function() {
        var ret = false;
        $(".input table input[type='text']").each(function () {
                var thisInputIsBlank = (
                    $(this).val().replace(/\s/g,'') == '' );
                if (thisInputIsBlank) ret = true;
                });
        return ret;
    }();
    if (!oneInputIsBlank) {
        makeNewInput();
        bindHandlers();
    }
};

var diaCheckboxChangeHandler = function() {
    var $checkbox = $(this);
    var checked = $checkbox.is(':checked')
    $checkbox.parent()[(checked?'add':'remove') + 'Class']('selected');
};

$.fn.hoverClass = function(className) {
    mouseoverHandler = function() { $(this).addClass(className); };
    mouseoutHandler = function() { $(this).removeClass(className); };
    return this.hover(mouseoverHandler, mouseoutHandler);
};

$.fn.debug = function() { console.debug(this); return this; }

var bindHandlers = function() {
    $(".input table input[type='text']").keydown(keydownHandler).debug();
    $(".input table input[type='checkbox']")
        .change(diaCheckboxChangeHandler);
    $(".input table td.data_source").hoverClass('hover');
};

$(bindHandlers);

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
    $.post(url, data, callback);
};

$.fn.setThrobberStatus = function(theStatus) {
    $cb = this;
    var $throbber = $cb.parent().find(
            '.data_import_status img');
    //console.debug("Trying to set status of throbber: ", $throbber.get(0));
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
    //console.debug($throbber.get(0));
};

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
};

var bindSubmitButtonClickHandler = function() {
    $('#submit_data_sources').click(submitDataSources);
};

$(bindSubmitButtonClickHandler);

// Create first blank row of input table.
$(makeNewInput);

$(function() { $('.hide_on_doc_ready').hide(); });
