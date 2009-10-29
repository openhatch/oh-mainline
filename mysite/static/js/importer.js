/* 
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
 *      (In the future.)
 *      (This code is handled in Preparation below.)
 *
 *  3.  When the user clicks the submit button, we ask the server
 *      to enqueue background tasks that import data from sources
 *      'round the web. 
 *      (This code is handled in Submission below.)
 *
 *  4.  When the server responds, we show some progress bars to
 *      the user, to let them know we're working behind the
 *      scenes.
 *      (This code is also handled in Submission below.)
 *
 *  5.  We ping the server repeatedly, asking
 *      "How's the import going? Are you done yet?"
 *
 *  6.  On each ping the server responds with a JSONified Python list comprising:
 *      - the Citations we've found so far
 *      - the DataImportAttempts used to find them
 *  
 *  7.  If all the DataImportAttempts read 'I'm done!',
 *      we tell the user "We're done!"
 */

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

var lastUniqueNumber = 0;
function generateUniqueID() {
    lastUniqueNumber++;
    return 'element_'+lastUniqueNumber;
}


makeNewInput = function() {
    // {{{
    var $form = $('form .body');
    var index = $form.find('.query').size();
    var extraClass = (index % 2 == 0) ? "" : " odd";
    var html = ""
        + "<div id='query_$INDEX' class='query"+ extraClass +"'>"
        // FIXME: Use $EXTRA_CLASS to include this in the string.
        + "   <div class='who'>"
        + "       <input type='text' name='identifier_$INDEX' />"
        + "   </div>"
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

bindHandlers = function() {
    // {{{
    $("form input[type='text']").keydown(keydownHandler);
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

enableThrobbersThenPollForStatusForever = function() {
    // {{{

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

/* Probably remove this.
diaCheckboxChangeHandler = function() {
    // {{{
    var $checkbox = $(this);
    var checked = $checkbox.is(':checked')
    $checkbox.parent()[(checked?'add':'remove') + 'Class']('selected');
    // }}}
};
*/

mockedPortfolioResponse = null;
askServerForPortfolio_wasCalled = false;
function askServerForPortfolio() {
    if (testJS) {
        updatePortfolio(mockedPortfolioResponse);
        return;
    }
    var ajaxOptions = {
        'type': 'GET',
        'url': '/profile/views/gimme_json_for_portfolio',
        'dataType': 'json',
        'success': updatePortfolio,
        'error': errorWhileAskingForPortfolio
    };
    $.ajax(ajaxOptions);
    askServerForPortfolio_wasCalled = true;
}

if (typeof testJS == 'undefined') { testJS = false; }

if (testJS) {
    // do nothing
} else {
    $(askServerForPortfolio);
}

function errorWhileAskingForPortfolio() {
    console.log('Error while asking for portfolio.');
}

/*
 * Perhaps we should talk more explicitly with the server about whose portfolio we want.
 * Otherwise somebody might do this:
 *  Log in as Alice
 *  Load portfolio
 *  In a different window, log out; log in as Bob
 *  Return to Alice's portfolio window
 *  Notice the portfolio are mixed together in an unholy UNION. Yow.
 */

function updatePortfolio(response) {
    /* Input: A whole bunch of (decoded) JSON data containing
     * all of the user's Citations, PortfolioEntries, and Projects,
     * summaries for those Citations, and DataImportAttempts.
     
     * Output: Nothing.

     * Side-effect: Update the page's DOM to display these data.
     * (FIXME: Right now we just add, not "update" :-)
     */
    var portfolio_entry_html = $('#portfolio_entry_building_block').html();
    var citation_html = $('#citation_building_block').html();
   
    /* Now fill in the template */
    
    for (var i = 0; i < response.portfolio_entries.length; i++) {
        var portfolioEntry = response.portfolio_entries[i];
	    /* portfolioEntry is something like: {'pk': 0, 'fields': {'project': 0}} 
	     * (a JSONified PortfolioEntry)
	     */
	    var id = 'portfolio_entry_' + portfolioEntry.pk;

        $new_portfolio_entry = $('#' + id);
        if ($new_portfolio_entry.size() == 0) {
            var $new_portfolio_entry = $(portfolio_entry_html);
            $('#portfolio').append($new_portfolio_entry);
            $new_portfolio_entry.attr('id', id);
            $new_portfolio_entry.attr('portfolio_entry__pk', portfolioEntry.pk);
        }
	    
        /* Find the project this PortfolioElement refers to */
	    var project_id = portfolioEntry.fields.project;
	    var project_we_refer_to = null;
	    $(response.projects).each( function() {
		    if (this.pk == project_id) {
			project_we_refer_to = this;
		    }
		});
	    /* project_description */
	    $(".project_description", $new_portfolio_entry).text(portfolioEntry.fields.project_description);
	    	   
	    /* project_icon */
        if (project_we_refer_to.fields.icon == '') {
            $new_portfolio_entry.find('.icon_flagger').remove();
        }
        else {
            $(".project_icon", $new_portfolio_entry).attr('src', "/static/"+project_we_refer_to.fields.icon);
        }
	    
	    /* project_name */
	    $(".project_name", $new_portfolio_entry).text(project_we_refer_to.fields.name);
	    
	    /* experience_description */
	    $(".experience_description", $new_portfolio_entry).text(
                portfolioEntry.fields.experience_description);

        /* Add the appropriate citations to this portfolio entry. */
        var addMemberCitations = function() {
            var citation = this;
            // "this" is an object in response.citations
            if ("portfolio_entry_"+citation.fields.portfolio_entry == 
                    $new_portfolio_entry.attr('id')) {
                // Does this exist? If not, then create it.
                var id = 'citation_' + citation.pk;
                var $citation_existing_or_not = $('#'+id);
                var already_exists = ($citation_existing_or_not.size() != 0);
                if (already_exists) {
                    var $citation = $citation_existing_or_not;
                }
                else {
                    // Then we have a citation that we're gonna add the DOM.
                    var $citation = $(citation_html);
                    $citation.attr('id', id);
                    if (citation.fields.is_published == '1') {
                        $citation.removeClass("unpublished");
                    }
                    $('.citations', $new_portfolio_entry).append($citation);
                }

                var summary = response.summaries[citation.pk]
                $citation.find('.summary').text(summary);
            }
        };
        $(response.citations).each(addMemberCitations);

	}
    setEventHandlers();
};

Citation = {};
Citation.$get = function(id) {
    var selector = '#citation_'+id;
    var matching = $(selector);
    fireunit.ok(matching.size() == 1, "Got just 1 citation with id = " + selector)
    return matching; 
};
Citation.get = function(id) {
    citation = Citation.$get(id).get(0);
    return citation;
};
Citation.$getDeleteLink = function(id) {
    $link = Citation.$get(id).find('a.delete_citation');
    return $link;
};

deleteCitationByID = function(id) {
    deleteCitation(Citation.$get(id));
};
deleteCitation = function($citation) {
    $citation.removeClass('unpublished')
        .removeClass('published')
        .addClass('deleted');
    fireunit.ok($citation.size() == 1, "deleteCitation asserts: there is a citation "
            + "that we're about to delete.");
    var pk = $citation[0].id.split('_')[1];
    var ajaxOptions = {
        'type': 'POST',
        'url': '/profile/views/delete_citation_do',
        'data': {'citation__pk': pk},
        'success': deleteCitationCallback,
        'error': deleteCitationErrorCallback,
    };
    $.ajax(ajaxOptions);
};
deleteCitationCallback = function (response) {
    // No need to do anything. We already marked
    // the citation with the css class 'deleted'.
};

deleteCitationErrorCallback = function (request) {
    Notifier.displayMessage('Whoops! There was an error ' +
            'communicating with the server when trying to ' +
            'delete a citation. The page may be out of date. ' +
            'Please reload. ');

};

drawAddCitationForm = function() {
    console.log("draw 'Add a citation' form");
};

Notifier = {};
Notifier.displayMessage = function(message) {
    $.jGrowl(message, {'life': 2000});
};

/******************
 * Event handlers *
 ******************/ 

deleteCitationForThisLink = function () {
    var deleteLink = this;
    var $citation = $(this).closest('.citations > li');
    deleteCitation($citation);
    return false; // FIXME: Test this.
};
drawAddCitationFormNearThisButton = function () {
    var button = this;
    var $citationForms = $(this).closest('.citations-wrapper').find('ul.citation-forms');
    fireunit.ok($citationForms.size() == 1, "there's one ul called 'citations-forms' in this wrapper");
    var buildingBlockHTML = $('#citation_form_building_block').html();
    var $form_container = $(buildingBlockHTML);

    // Set element ID
    $form_container.attr('id', generateUniqueID());

    $citationForm = $form_container.find('form');
   
    $citationForms.append($form_container);

    console.log($citationForm);

    console.log($citationForm.parents('.portfolio_entry'));

    // Set field: portfolio entry ID
    var portfolioEntryID = $citationForm.closest('.portfolio_entry')
        .attr('portfolio_entry__pk');
    $citationForm.find('[name="portfolio_entry"]').attr('lang', 'your-mom');
    $citationForm.find('[name="portfolio_entry"]').attr('value', portfolioEntryID);
    console.log('hi');
    console.log($citationForm.find('[name="portfolio_entry"]'));

    // Set field: form container element ID
    var formContainerElementID = $citationForm.closest('.citation-forms li').attr('id');
    $citationForm.find('[name="form_container_element_id"]').val(formContainerElementID);

    var ajaxOptions = {
        'success': handleServerResponseToNewRecordSubmission,
        'error': handleServerErrorInResponseToNewRecordSubmission,
        'dataType': 'json'
    };
    $citationForm.submit(function() {
            $(this).ajaxSubmit(ajaxOptions);
            $(this).find('input').attr('disabled','disabled');
            return false;});

    return false; // FIXME: Test this.
}

handleServerResponseToNewRecordSubmission = function(response) {
    askServerForPortfolio();
    $form_container = $('#'+response.form_container_element_id);
    $form_container.remove();
};
handleServerErrorInResponseToNewRecordSubmission = function(xhr) {
    responseObj = $.secureEvalJSON(xhr.responseText);

    var msg = 'There was at least one problem submitting your citation: <ul>';
    for (var i = 0; i < responseObj.error_msgs.length; i++) {
        msg += "<li class='error-message'>"
            + responseObj.error_msgs[i]
            + "</li>";
    }
    msg += "</ul>";

    $citationFormContainer = $('#'+responseObj.form_container_element_id);
    $citationFormContainer.find('input').removeAttr('disabled');

    // FIXME: XSS vulnerability? This will work:
    // msg += "<script>alert('injection');</script>";
    Notifier.displayMessage(msg);
};

FlagIcon = {};
FlagIcon.postOptions = {
    'url': '/profile/views/replace_icon_with_default',
    'type': 'POST',
    'dataType': 'json',
};
FlagIcon.postOptions.success = function (response) {
    $portfolioEntry = $('#portfolio_entry_'+response['portfolio_entry__pk']);
    var defaultIconSrc = $('#portfolio_entry_building_block img.project_icon').attr('src');
    $portfolioEntry.find('img.project_icon').attr('src', defaultIconSrc);

    // the text() function will remove all children, including the link.
    $portfolioEntry.find('.icon_flagger').text('Using default icon.');
};
FlagIcon.postOptions.error = function (response) {
    alert('error');
};
FlagIcon.post = function () {
    $.ajax(FlagIcon.postOptions);
};
FlagIcon.flag = function () {
    var $flaggerLink = $(this);

    FlagIcon.postOptions.data = {
        'portfolio_entry__pk': $flaggerLink.closest('.portfolio_entry')
            .attr('portfolio_entry__pk')
    };
    FlagIcon.post();
    return false;
};
FlagIcon.setEventHandlers = function() {
    $('.icon_flagger a').click(FlagIcon.flag);
};

HowTo = {
    'init': function () {
        HowTo.$element = $('#portfolio .howto');
        HowTo.$hideLink = $('#portfolio .howto .hide-link');
        HowTo.$showLink = $('#portfolio .show-howto-link');

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

PortfolioEntry = {};
PortfolioEntry.setEventHandlers = function() {
    PortfolioEntry.Save.setEventHandlers();
    PortfolioEntry.Delete.setEventHandlers();
};

PortfolioEntry.Save = {};
PortfolioEntry.Save.postOptions = {
    'url': '/profile/views/save_portfolio_entry_do',
    'type': 'POST',
    'dataType': 'json',
};
PortfolioEntry.Save.postOptions.success = function (response) {
    Notifier.displayMessage('Portfolio entry saved.');
};
PortfolioEntry.Save.postOptions.error = function (response) {
    Notifier.displayMessage('Oh dear! There was an error saving this entry in your portfolio. '
            + 'A pox on the programmers.');
};
PortfolioEntry.Save.post = function () {
    $.ajax(PortfolioEntry.Save.postOptions);
};
PortfolioEntry.Save.save = function () {
    $saveLink = $(this);
    $pfEntry = $saveLink.closest('.portfolio_entry');
    PortfolioEntry.Save.postOptions.data = {
        'portfolio_entry__pk': $pfEntry.attr('portfolio_entry__pk'),
        'project_description': $pfEntry.find('.project_description').val(),
        'experience_description': $pfEntry.find('.experience_description').val()
    };
    PortfolioEntry.Save.post();
    return false;
}
PortfolioEntry.Save.setEventHandlers = function() {
    $('.portfolio_entry a.publish').click(PortfolioEntry.Save.save);
};

PortfolioEntry.Delete = {};
PortfolioEntry.Delete.postOptions = {
    'url': '/profile/views/delete_portfolio_entry_do',
    'type': 'POST',
    'dataType': 'json',
};
PortfolioEntry.Delete.postOptions.success = function (response) {
    if (!response.success) {
        PortfolioEntry.Delete.postOptions.error(response);
        return;
    }
    /* Find the portfolio entry section of the page, and make it disappear. */
    var pk = response.portfolio_entry__pk;
    $portfolioEntry = $('#portfolio_entry_'+pk);
    $portfolioEntry[0].style.display = 'none';
    Notifier.displayMessage('Portfolio entry deleted.');
};
PortfolioEntry.Delete.postOptions.error = function (response) {
    Notifier.displayMessage('Oh snap! We failed to delete your PortfolioEntry.');
};
PortfolioEntry.Delete.post = function () {
    $.ajax(PortfolioEntry.Delete.postOptions);
};
PortfolioEntry.Delete.delete = function () {
    $deleteLink = $(this);
    $pfEntry = $deleteLink.closest('.portfolio_entry');
    PortfolioEntry.Delete.postOptions.data = {
        'portfolio_entry__pk': $pfEntry.attr('portfolio_entry__pk'),
    };
    PortfolioEntry.Delete.post();
    return false;
}
PortfolioEntry.Delete.setEventHandlers = function() {
    $('.portfolio_entry .actions a.delete').click(PortfolioEntry.Delete.delete);
};


setEventHandlers = function() {
    $('a.delete_citation').click(deleteCitationForThisLink);
    $('.citations-wrapper .add').click(drawAddCitationFormNearThisButton);
    FlagIcon.setEventHandlers();
    PortfolioEntry.setEventHandlers();
    Citation.setEventHandlers();
};
$(setEventHandlers);

Citation.setEventHandlers = function() {
    Citation.HowTo.setEventHandlers();
};
Citation.HowTo = {};
Citation.HowTo.hideAll = function () {
    $('.citations-wrapper .howto').hide();
    $('.citations-wrapper a.show_howto').show();
    return false;
};
Citation.HowTo.showMyHowto = function () {
    $showLink = $(this);
    $showLink.parent().find('.howto').show();
    $showLink.hide();
    return false;
};
Citation.HowTo.setEventHandlers = function () {
    $('.citations-wrapper .howto a.hide_me').click(Citation.HowTo.hideAll);
    $('.citations-wrapper a.show_howto').click(Citation.HowTo.showMyHowto);
};

// vim: set nu:
