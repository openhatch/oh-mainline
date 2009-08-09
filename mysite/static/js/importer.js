/* 
 * {{{
 * Ze importer.
 *
 * == Dependencies ==
 *  * jQuery <http://jquery.com>
 *  * the jQuery Form Plugin <http://malsup.com/jquery/form/#code-samples>
 *
 * == The order of things ==
 *
 *  1.  User enters an identifier (username or email address)
 *      into an input field.
 *
 *  2.  When the user exits the input field, we grab as much
 *      data as we can about that identifier.
 *      (This code is handled in Preparation below.)
 *
 *  3.  The user selects/deselects some checkboxes.
 *
 *  4.  When the user clicks the submit button, we set the 
 *      'person_wants_data' field of their DataImportAttempts
 *      according to which checkboxes they've clicked.
 *      (This code is handled in Submission below.)
 *
 *  5.  When the server responds, we show some throbbers to
 *      the user, to let them know we're working behind the
 *      scenes.
 *      (This code is also handled in Submission below.)
 *
 *  6.  We ping the server repeatedly, asking "Are you done yet?"
 *
 *  7.  On each ping the server responds with a list of DIAs and
 *      their attributes.
 *
 *  8.  If all the DIAs read 'I'm done!', we encourage the user
 *      to visit his/her portfolio.
 *  }}}
 */

getStrings = function(schema, dictionaries) {
    // {{{
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
     *  getStrings(dictionaries, schema);
     *
     * </input>
     *
     * <output>
     * // Array of strings.
     * [
     *      "In French, hello is 'Salut', goodbye is 'A tout à l'heure', \
     *          thank you is 'Merci beaucoup'",
     *      "In Turkish... etc.",
     *      "In Yiddish... etc."
     * ]
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
    // }}}
};

makeNewInput = function() {
    // {{{
    var $form = $('form .body');
    var index = $form.find('.query').size();
    var extraClass = (index % 2 == 0) ? "" : " odd";
    var html = ""
        + "<div id='query_$INDEX' class='query"+ extraClass +"'>"
        + "   <div class='who'>"
        + "       <input type='text' name='identifier_$INDEX' />"
        + "   </div>"
        + "   <ul class='data_sources'>"

    var imgPrefix = "/static/images/icons/data-sources/";
    var sourceDictionaries = [
        {
            '$ID': 'rs',
            '$DISPLAY': "<span>All repositories</span>"
        },
        {
            '$ID': 'lp',
            '$DISPLAY': "<img src='"
                + imgPrefix + "launchpad.png' alt='Launchpad' />"
        },
        {
            '$ID': 'ou',
            '$DISPLAY': "<img src='"
                + imgPrefix + "ohloh.png' alt='Ohloh' />"
        },
    ];

    var checkboxTDSchema = ""
        + "       <li class='data_source selected'>"
        + "            <input type='checkbox' checked "
        + "                name='person_wants_$INDEX_$ID' "
        + "                id='person_wants_$INDEX_$ID' />"
        + "            <label for='person_wants_$INDEX_$ID'>"
        + "                $DISPLAY"
        + "            </label>"
        + "       </li>";

    html += getStrings(checkboxTDSchema, sourceDictionaries).join("\n")
        + "    </ul>"
        + "</div>";

    html = html.replace(/\$INDEX/g, index);

    $(html).appendTo($form);

    bindHandlers();
    // }}}
};

keydownHandler = function() {
    // {{{
    $input = $(this);
    var oneInputIsBlank = function() {
        var ret = false;
        $("form input[type='text']").each(function () {
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
    // }}}
};

diaCheckboxChangeHandler = function() {
    // {{{
    var $checkbox = $(this);
    var checked = $checkbox.is(':checked')
    $checkbox.parent()[(checked?'add':'remove') + 'Class']('selected');
    // }}}
};

$.fn.hoverClass = function(className) {
    // {{{
    mouseoverHandler = function() { $(this).addClass(className); };
    mouseoutHandler = function() { $(this).removeClass(className); };
    return this.hover(mouseoverHandler, mouseoutHandler);
    // }}}
};

$.fn.debug = function() {
    // {{{
    console.debug(this);
    return this;
    // }}}
};

bindHandlers = function() {
    // {{{
    $("form input[type='text']").keydown(keydownHandler);
    $("form input[type='checkbox']")
        .change(diaCheckboxChangeHandler);
    $("form .data_source").hoverClass('hover');
    // }}}
};

$.fn.setThrobberStatus = function(theStatus) {
    // {{{
    var $throbber = this;
    mapStatusToImage = {
        'working': '/static/images/snake.gif',
        'succeeded': '/static/images/icons/finished-successfully.png',
        'failed': '/static/images/icons/finished-unsuccessfully.png',
    }
    src = mapStatusToImage[theStatus];
    if ($throbber.attr('src') != src) {
        $throbber.attr('src', src);
    }
    // }}}
};

$.fn.convertCheckboxesToThrobber = function() {
    // {{{
    var convert = function () {
        var $checkbox = $(this);
        bits = $checkbox.attr('id').split('_');
        var query_index = bits[2];
        var query = $('input[type="text"]').get(query_index).value;

        // Skip checkboxes whose queries are blank.
        if (query.replace(/\s/g, '') == '') return;

        var source = bits[3];
        var imageHTML = "<img class='throbber' src='/static/images/snake.gif'/>";
        var $throbber = $(imageHTML).insertBefore($checkbox);
        $throbber.data('query', query);
        $throbber.data('source', source);
        $checkbox.remove();
    };
    return this.each(convert);
    // }}}
};

enableThrobbersThenPollForStatusForever = function() {
    // {{{
    var $checkboxes = $("#importer form input[type='checkbox']:checked");
    // Enable throbbers.
    $checkboxes.convertCheckboxesToThrobber();

    // Ask server for a list of dias, which will tell us
    // which importation background jobs have finished,
    // and if they finished successfully.
    var are_they_done_url = "/people/gimme_json_that_says_that_commit_importer_is_done";
    var allDone = undefined;
    var ask_if_done = function () {
        console.log('Asking if done yet.');
        var callback = function(dias) {
            var allSeemsDone = true;
            /*console.log(dias);*/
            for (var d = 0; d < dias.length; d++) {
                var dia = dias[d];
                /*console.debug("while polling for status, server returned this dia", dia);*/
                var $throbber = $('');
                /*console.debug("while polling for status, attempted to set status of throbber for checkbox: ", $checkbox.get(0));*/
                var diaStatus = null;
                if (dia.fields.completed) {
                    diaStatus = dia.fields.failed ? "failed" : "succeeded";
                }
                else {
                    diaStatus = 'working';
                }
                $(findThrobbersForDia(dia)).each(function () {
                        $(this).setThrobberStatus(diaStatus);
                        });
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
            $('#jobs-are-done').show();
        }
    }
    window.askIfDoneInterval = window.setInterval(ask_if_done, 1000);
    // }}}
};

findThrobbersForDia = function(dia) {
    var $throbbers = $('.throbber');
    var matching = [];
    var pushIfMatch = function () {
        $throbber = $(this);
        if ($throbber.data('query') == dia.fields.query
                && $throbber.data('source') == dia.fields.source) {
            matching.push($throbber);
        }
    };
    $throbbers.each(pushIfMatch);
    return matching;
};

Preparation = {
    // {{{
    'init': function () {
        Preparation.$inputs = $('#importer form input[type="text"]');
        Preparation.bindHandler();
    },
    '$inputs': null,
    'handler': function () {
        var url = '/people/portfolio/import/prepare_data_import_attempts_do';
        var query = $(this).val();
        fireunit.ok(typeof query != 'undefined', "query: " + query);

        var data = {'format': 'success_code'};

        // About the below; the old POST handler used to expect
        // a digit instead of "x", but I don't think it will matter.
        data['commit_username_x'] = query;

        $.post(url, data, Preparation.callback);
    },
    'bindHandler': function () {
        Preparation.$inputs.blur(Preparation.handler);
    },
    'callback': function (response) {
    }
    // }}}
};

Submission = {
    // {{{
    'init': function () {
        Submission.$form = $('#importer form');
        Submission.bindHandler();
    },
    '$form': null,
    'handler': function () {
        $(this).ajaxSubmit({'success': Submission.callback});
        return false; // Bypass the form's native Submission logic.
    },
    'bindHandler': function () {
        Submission.$form.submit(Submission.handler);
    },
    'callback': function (response) {
        enableThrobbersThenPollForStatusForever();
        $('input', Submission.$form).attr('disabled', 'disabled');
    }
    // }}}
};

init = function () {
    makeNewInput(); // Create first blank row of input table.
    Preparation.init();
    Submission.init();
};
$(init);

$(function() { $('.hide_on_doc_ready').hide(); });

HowTo = {
    'init': function () {
        HowTo.$element = $('#importer .howto');
        HowTo.$hideLink = $('#importer .howto .hide-link');
        HowTo.$showLink = $('#importer .show-howto-link');

        var tests = ["HowTo.$element.size() == 1",
                "HowTo.$hideLink.size() == 1",
                "HowTo.$showLink.size() == 1"];
        for (var i = 0; i < tests.length; i++) {
            fireunit.ok(eval(tests[i]), tests[i]);
        }

        for (var e in HowTo.events) {
            HowTo.events[e].bind();
        }
    },
    '$element': null,
    '$hideLink': null,
    '$showLink': null,
    'events': {
        'hide': {
            'go': function () {
                HowTo.$element.fadeOut('slow');
                HowTo.$showLink.fadeIn('slow');
                return false;
            },
            'bind': function () {
                HowTo.$hideLink.click(HowTo.events.hide.go);
            },
        },
        'show': {
            'go': function () {
                HowTo.$element.fadeIn('slow');
                return false;
            },
            'bind': function () {
                HowTo.$showLink.click(HowTo.events.show.go);
            },
        }
    }
};
$(HowTo.init);

tests = {
    'Preparation': function () {
        $('form input[type="text"]').val('paulproteus').blur();
        fireunit.testDone();
    }
};
runTests = function () {
    for (t in tests) {
        fireunit.ok(true, "test: " + t);
        tests[t](); 
    }
};
//$(runTests);
