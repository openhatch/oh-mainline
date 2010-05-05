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

if (typeof want_importer == 'undefined') {
    /* do nothing. */
} else {

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

$.fn.textSmart = function(text) {
    // Only replace text if text is different.
    if (this.text() != text) { this.text(text); }
};

$.fn.htmlSmart = function(html) {
    // Only replace html if html is different.
    if (this.html() != html) { this.html(html); }
};

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

    $('#portfolio_entries .loading_message').hide();
   
    /* Now fill in the template */
    
    if (response.portfolio_entries.length === 0) {
        $('#portfolio_entries .apologies').show();
    }

    $('#reorder_projects_wrapper')[(response.portfolio_entries.length > 1) ? "show" : "hide"]();

    var are_we_printing_archived_projects_yet = false;

    for (var i = 0; i < response.portfolio_entries.length; i++) {

        var portfolioEntry = response.portfolio_entries[i];
	    /* portfolioEntry is something like: {'pk': 0, 'fields': {'project': 0}} 
	     * (a JSONified PortfolioEntry)
	     */
	    var id = 'portfolio_entry_' + portfolioEntry.pk;

        $new_portfolio_entry = $('#' + id);
        if ($new_portfolio_entry.size() == 0) {

            // The HTML must be customized a bit for this portfolio entry so
            // that labels know which descriptions to point to.
            var html = portfolio_entry_html.replace(/\$PORTFOLIO_ENTRY_ID/g, portfolioEntry.pk);
            var $new_portfolio_entry = $(html);
            $('#portfolio_entries').append($new_portfolio_entry);
            $new_portfolio_entry.attr('id', id);
            $new_portfolio_entry.attr('portfolio_entry__pk', portfolioEntry.pk);
        }

        // if the last one wasn't archived but this one is, add a heading
        if (! are_we_printing_archived_projects_yet && portfolioEntry.fields.is_archived) {
            var heading = $('#archived_projects_heading');
            if (heading.size() == 0) {
                heading = $('<h5 id=\'archived_projects_heading\'>Archived projects</h5>');
            }
            $new_portfolio_entry.before(heading);
            are_we_printing_archived_projects_yet = true;
        }

        // published/unpublished status
        if (portfolioEntry.fields.is_published) {
            var $actionListItem = $new_portfolio_entry.find('.actions li.publish_portfolio_entry');
            var $maybeSpan = $actionListItem.find('span');

            $new_portfolio_entry.removeClass("unpublished");

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
	    $(".project_description", $new_portfolio_entry).textSmart(portfolioEntry.fields.project_description);

	    /* project_icon */
        if (project_we_refer_to.fields.icon_for_profile == '') {
            $new_portfolio_entry.find('.icon_flagger').hide();
        }
        else {
            /* So, the object we select is a DIV whose CSS background-image
             * is what causes the browser to display the icon. We store a
             * copy of the URL JavaScript gave us in a totally made-up "src"
             * attribute of the DIV to make life easier for us.
             */
            var $icon = $new_portfolio_entry.find(".project_icon");
            var current_src = $icon.attr('src');
            var response_src = ("/static/" +
                    project_we_refer_to.fields.icon_for_profile);
            var response_src_for_css = 'url(' + response_src + ')';
            if (current_src != response_src) {
                $icon.attr('src', response_src); /* just for us */
                $icon.css('background-image', response_src_for_css);
                $new_portfolio_entry.find('.icon_flagger').show();
            }
        }
	    
	    /* project_name */
	    $(".project_name", $new_portfolio_entry).textSmart(
                project_we_refer_to.fields.name);
	    
	    /* experience_description */
	    $(".experience_description", $new_portfolio_entry).textSmart(
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
                } else {
                    // Then we have a citation that we're gonna add the DOM.
                    var $citation = $(citation_html);
                    $citation.attr('id', id);
                    $('.citations', $new_portfolio_entry).append($citation);
                }

                // Update the css class of this citation to reflect its
                // published/unpublished status.
                if (citation.fields.is_published == '1') {
                    $citation.removeClass("unpublished");
                } else {
                    // Citation is unpublished
                    $new_portfolio_entry.addClass('unsaved');
                }

                var summaryHTML = response.summaries[citation.pk]
                $summary = $citation.find('.summary');
                $summary.htmlSmart(summaryHTML);
            }
        };
        $(response.citations).each(addMemberCitations);

	}

    if (response['import'].running) {
        Importer.ProgressBar.showWithValue(response['import'].progress_percentage);
        window.setTimeout(askServerForPortfolio, 1500);
    }
    else {
        // If import's not running, bump to 100.
        // If no import was running in the first place, then the progress bar will remain invisible.
        // If there had been an import running, then the progress bar, now visible, will
        // stand at 100%, to indicate that the import is done.
        Importer.ProgressBar.bumpTo100();
    }

    bindEventHandlers();

    if (typeof response.messages != 'undefined') {
        for (var m = 0; m < response.messages.length; m++) {
            Notifier.displayMessage(response.messages[m]);
        };
    }

    SaveAllButton.updateDisplay();

    var conditions = PortfolioEntry.Save.stopCheckingForNewIconsWhenWeAllReturnTrue;
    var all_are_true = true;
    for (var c = 0; c < conditions.length; c++) {
        if (!conditions[c](response)) { all_are_true = false; break; }
    }
    if (!all_are_true) {
        window.setTimeout(askServerForPortfolio, 1500);
    }
    else {
        PortfolioEntry.Save.stopCheckingForNewIconsWhenWeAllReturnTrue = [];
    }

};

Citation = {};
Citation.$get = function(id) {
    var selector = '#citation_'+id;
    var matching = $(selector);
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
    $citation.addClass('deleted').fadeOut('slow', function () {
        $(this).remove();
    });

    /*removeClass('unpublished')
        .removeClass('published')
        .addClass('deleted');*/
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
    // No need to do anything. We already 
    // removed the citation element.
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
    $.jGrowl(message, {'life': 5000});
};

/******************
 * Event handlers *
 ******************/ 

deleteCitationForThisLink = function () {
    if (!confirm('are you sure?')) return false;
    var deleteLink = this;
    var $citation = $(this).closest('.citations > li');
    deleteCitation($citation);
    return false; 
};
drawAddCitationFormNearThisButton = function () {
    var button = this;
    var $citationForms = $(this).closest('.citations-wrapper').find('ul.citation-forms');
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
    var defaultIconCssAttr = $('#portfolio_entry_building_block .project_icon').css('background-image');
    var defaultIconUrl = defaultIconCssAttr.replace(/^url[(]/, '').replace(/[)]$/, ''); /* remove url() */
    var relative_path = defaultIconUrl.replace(/^.*?:[/][/].*?[/]/, '/'); /* remove http://domain or https://domain */
    // we change the image url as the icon div understands it twice
    // this is a hack that allows us to change fewer tests (the icon used to be an img)
    $portfolioEntry.find('.project_icon').attr('src', relative_path);
    $portfolioEntry.find('.project_icon').css('background-image', defaultIconCssAttr);

    // the text() function will remove all children, including the link.
    $portfolioEntry.find('.icon_flagger').text('Using default icon.');
};
FlagIcon.postOptions.error = function (response) {
    alert('error');
};
FlagIcon.post = function () {
    if (!confirm("Flag icon as incorrect: This will remove the icon - are you sure?"))
        { return false; }
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
FlagIcon.bindEventHandlers = function() {
    $('.icon_flagger a').click(FlagIcon.flag);
};

// Despite the name, this is actually the Importer
// FIXME: Rename this "Importer"
HowTo = {
    'init': function () {
        HowTo.$element = $('#portfolio_entries .howto');
        HowTo.$hideLink = $('#portfolio_entries .howto .hide-link');
        HowTo.$showLink = $('#portfolio_entries .show-howto-link');

        var tests = ["HowTo.$element.size() == 1",
                "HowTo.$hideLink.size() == 1",
                "HowTo.$showLink.size() == 1"];
        for (var i = 0; i < tests.length; i++) {
            // fireunit.ok(eval(tests[i]), tests[i]);
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
PortfolioEntry.bindEventHandlers = function() {
    PortfolioEntry.Save.bindEventHandlers();
    PortfolioEntry.Delete.bindEventHandlers();
    $('#portfolio_entries .portfolio_entry textarea').keydown(pfEntryFieldKeydownHandler);
};

pfEntryFieldKeydownHandler = function () {
    var $textarea = $(this);
    $textarea.closest('.portfolio_entry').not('.unpublished, .unsaved').addClass('unsaved');
    SaveAllButton.updateDisplay();
};

PortfolioEntry.Save = {};
PortfolioEntry.Save.postOptions = {
    'url': '/profile/views/save_portfolio_entry_do',
    'type': 'POST',
    'dataType': 'json',
};
PortfolioEntry.Save.stopCheckingForNewIconsWhenWeAllReturnTrue = [];
PortfolioEntry.Save.postOptions.success = function (response) {
    if (typeof response.pf_entry_element_id != 'undefined') {
        // This was an INSERT aka an "Add"
        var $new_pf_entry = $('#'+response.pf_entry_element_id);
        $new_pf_entry.attr('id', "portfolio_entry_"+response.portfolio_entry__pk);
        $new_pf_entry.attr('portfolio_entry__pk', response.portfolio_entry__pk);
        $old_project_name_field = $new_pf_entry.find('input:text.project_name');
        var project_name = $old_project_name_field.val()
        $new_project_name_span = $('<span></span>').addClass('project_name')
            .text(project_name);
        $old_project_name_field.replaceWith($new_project_name_span);

        var iconLookupIsOver = function (project_name) {
            return function (portfolio_json) { 
                for (var p = 0; p < portfolio_json.projects.length; p++) {
                    var project = portfolio_json.projects[p];
                    if (project.fields.name.toLowerCase() == project_name.toLowerCase()) {
                        var new_date = project.fields.date_icon_was_fetched_from_ohloh;
                        if (new_date === null) { return false; }
                        else { return true; }
                    }
                }
            }
        }(project_name);
        PortfolioEntry.Save.stopCheckingForNewIconsWhenWeAllReturnTrue.push(iconLookupIsOver);
    }
    var $entry = $('#portfolio_entry_'+response.portfolio_entry__pk);
    $entry.removeClass('unsaved').removeClass('adding');
    var project_name = $entry.find('.project_name').text();
    Notifier.displayMessage('Saved entry for '+project_name+'.');

    // Poll until we stop looking for an icon
    window.checkForNewIconsRepeatedly = window.setTimeout(askServerForPortfolio, 1500);
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

    // Do some client-side validation.
    $projectName = $pfEntry.find('input.project_name');
    if ($projectName.size() === 1) {
        if ($projectName.val() === $projectName.attr('title')) {
            alert("Couldn't save one of your projects. Did you forget to type a project name?");
            return false;
        }
    }
    PortfolioEntry.Save.postOptions.data = {
        'portfolio_entry__pk': $pfEntry.attr('portfolio_entry__pk'),
        'project_name': $pfEntry.find('.project_name').val(),
        'project_description': $pfEntry.find('.project_description').val(),
        'experience_description': $pfEntry.find('.experience_description').val(),

        // Send this always, but really it's only used when the pf entry has no pk yet.
        'pf_entry_element_id': $pfEntry.attr('id'), 
    };
    PortfolioEntry.Save.post();
    return false;
}
PortfolioEntry.Save.bindEventHandlers = function() {
    $('.portfolio_entry li.publish_portfolio_entry a').click(PortfolioEntry.Save.save);
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
    project_name = $portfolioEntry.find('.project_name').text();
    $portfolioEntry.hide();
    Notifier.displayMessage('Deleted entry for '+project_name+'.');
    SaveAllButton.updateDisplay();
};
PortfolioEntry.Delete.postOptions.error = function (response) {
    Notifier.displayMessage('Oh snap! We failed to delete your PortfolioEntry.');
};
PortfolioEntry.Delete.post = function () {
    $.ajax(PortfolioEntry.Delete.postOptions);
};
PortfolioEntry.Delete.deleteIt = function (deleteLink) {
    $deleteLink = $(deleteLink);
    $pfEntry = $deleteLink.closest('.portfolio_entry');
    if ($pfEntry.hasClass('adding')) {
        // If this pfEntry element is in adding mode,
        // then there is no corresponding record in the db to delete,
        // so let's just remove the element and say no more.
        $pfEntry.remove();
    }
    else {
        PortfolioEntry.Delete.postOptions.data = {
            'portfolio_entry__pk': $pfEntry.attr('portfolio_entry__pk'),
        };
        PortfolioEntry.Delete.post();
    }
    return false;
}
PortfolioEntry.Delete.bindEventHandlers = function() {
    $('.portfolio_entry .actions li.delete_portfolio_entry a').click(function(){
        var deleteLink = this;
        keep_going = confirm('are you sure?');
        if(keep_going){
            PortfolioEntry.Delete.deleteIt(deleteLink);
            return false;
        }
        else{
            return false;
        }
    });
};


bindEventHandlers = function() {
    $('a.delete_citation').hover(
        function () { $(this).closest('.citations > li').addClass('to_be_deleted'); },
        function () { $(this).closest('.citations > li').removeClass('to_be_deleted'); }
    );
    $('a.delete_citation').click(deleteCitationForThisLink);
    $('.citations-wrapper .add').click(drawAddCitationFormNearThisButton);
    FlagIcon.bindEventHandlers();
    PortfolioEntry.bindEventHandlers();
};
$(bindEventHandlers);

Importer = {};
Importer.Inputs = {};
Importer.Inputs.getInputs = function () {
    return $("form#importer input[type='text']");
};
Importer.Inputs.init = function () {
    Importer.Inputs.makeNew();
    Importer.Inputs.makeNew();
    Importer.Inputs.getInputs().eq(0).attr('title',
            "Type a repository username here");
    Importer.Inputs.getInputs().eq(1).attr('title',
            "Type an email address here");
    Importer.Inputs.getInputs().hint();
};
Importer.Inputs.makeNew = function () {

    // Don't make more than three. FIXME: Make this work for n > 3.
    //if ($('#importer .query').size() > 2) return; 

    var $inputs_go_here = $('form#importer .body');
    var index = $inputs_go_here.find('.query').size();
    var extraClass = (index % 2 == 0) ? "" : " odd";
    var html = ""
        + "<div id='query_$INDEX' class='query"+ extraClass +"'>"
        // FIXME: Use $EXTRA_CLASS to include this in the string.
        + "   <div class='who'>"
        + "       <input type='text' "
        + "             name='identifier_$INDEX' />"
        + "   </div>"
        + "</div>";

    html = html.replace(/\$INDEX/g, index);

    $input_container = $(html);
    
    $('#importer-form-footer').before($input_container);

    Importer.Inputs.bindEventHandlers();

    return false;
};
Importer.Inputs.keydownHandler = function () {
    $input = $(this);
    var oneInputIsBlank = function() {
        var ret = false;
        $("form#importer input[type='text']").each(function () {
                var thisInputIsBlank = (
                    $(this).val().replace(/\s/g,'') == '' 
                    || $(this).val() == $(this).attr('title'));
                if (thisInputIsBlank) ret = true;
                });
        return ret;
    }();
    if (!oneInputIsBlank) {
        Importer.Inputs.makeNew();
        Importer.Inputs.bindEventHandlers();
    }
};
Importer.Inputs.bindEventHandlers = function () {
    $("form#importer input[type='text']").keydown(Importer.Inputs.keydownHandler);
};

$(Importer.Inputs.init);

Importer.Submission = {
    'init': function () {
        Importer.Submission.$form = $('form#importer');
        Importer.Submission.bindEventHandlers();
    },
    '$form': null,
    'postOptions': {
        'success': function () {
            askServerForPortfolio();
        },
        'error': function () {
            Notifier.displayMessage("Apologies&mdash;there was an error starting this import.");
        }
    },
    'submitHandler': function () {
        $(this).ajaxSubmit(Importer.Submission.postOptions);
        return false; // Bypass the form's native submission logic.
    },
    'bindEventHandlers': function () {
        Importer.Submission.$form.submit(Importer.Submission.submitHandler);
    },
};
$(Importer.Submission.init);

Importer.ProgressBar = {};
Importer.ProgressBar.showWithValue = function(value) {
    $bar = $('#importer #progressbar');
    if (value < 10 ) { value = 10; } // Always show a smidgen of progress.
    $bar.addClass('working');
    if (value == 100) { Importer.ProgressBar.bumpTo100(); }
    else { $bar.show().progressbar('option', 'value', value); }
};
Importer.ProgressBar.bumpTo100 = function() {
    $('#importer #progressbar').removeClass('working').progressbar('option', 'value', 100);
};

PortfolioEntry.Add = {};
PortfolioEntry.Add.$link = null;
PortfolioEntry.Add.$projectNames = null;
PortfolioEntry.Add.init = function () {
    console.info('console me');
    PortfolioEntry.Add.$link = $('a#add_pf_entry');
    PortfolioEntry.Add.bindEventHandlers();
};
// We do this so that this particular method can be monkeypatched in testDeleteAdderWidget.
PortfolioEntry.Add.whenDoneAnimating = function () { SaveAllButton.updateDisplay(); };

PortfolioEntry.Add.clickHandler = function (project_name) {
    // Draw a widget for adding pf entries.
    var html = $('#add_a_portfolio_entry_building_block').html();
    $add_a_pf_entry = $(html);
    $add_a_pf_entry.attr('id', generateUniqueID());
    $('#portfolio_entries').prepend($add_a_pf_entry);

    if (typeof project_name == 'string') {
        // Fill the project name
        $add_a_pf_entry.find('.project_name').eq(0).val(project_name);
        $add_a_pf_entry.show(PortfolioEntry.Add.whenDoneAnimating);
    }
    else {
        // project_name not specified or is an event 
        $add_a_pf_entry.hide().fadeIn(PortfolioEntry.Add.whenDoneAnimating);
    }

    PortfolioEntry.bindEventHandlers();
    $add_a_pf_entry.find('input[title]').hint();

    return false;
};

PortfolioEntry.Add.bindEventHandlers = function () {
    PortfolioEntry.Add.$link.click(PortfolioEntry.Add.clickHandler);
};

$(PortfolioEntry.Add.init);

/*
 *      Re-order projects
 *-------------------------*/

PortfolioEntry.Reorder = {
    '$list': null,
    '$done_reordering': null,
    '$hideUsWhenSorting': null,
    'init': function () {

        PortfolioEntry.Reorder.$hideUsWhenSorting = $('#add_pf_entry,'
            + 'h4 .separator, .apologies, #back_to_profile, #import_links_heading, '
            + '#importer, #back_to_profile, #portfolio_entries,'
            + '#save_all_projects');

        $('a#reorder_projects').click(function () {

            if ($('#portfolio .unsaved, #portfolio .unpublished').size() > 0) {
                alert('Please save all of your projects before you sort or archive them.');
                return false;
            }

            $reorder_projects_link = $(this);

            // print a list of project names
            PortfolioEntry.Reorder.$list = $list = $('<ul id="projects_to_be_reordered">');
            var have_we_created_the_fold_yet = false;
            var create_the_fold = function () {
                $list.append("<li id='sortable_portfolio_entry_FOLD' class='fold'>(To archive your work on a project, put it below this line.)</li>");
            };
            $('#portfolio .portfolio_entry:visible, #archived_projects_heading').each(function () {
                if (this.id == 'archived_projects_heading') {
                    have_we_created_the_fold_yet = true;
                    create_the_fold();
                }
                else {
                    var project_name = $(this).find('.project_name').html();
                    var $item = $('<li>').html(project_name).attr('id', 'sortable_'+this.id);
                    $list.append($item);
                }
            });
            if (!have_we_created_the_fold_yet) { create_the_fold(); }

            $('#portfolio_entries').before($list);
            PortfolioEntry.Reorder.$hideUsWhenSorting.hide();

            // Make list sortable using jQuery UI
            $list.sortable({'axis': 'y'});

            $reorder_projects_link.hide();

            $('#projects_heading span:eq(0)').text('Sort and archive projects');

            $('#done_reordering').text('Save this ordering').removeAttr('disabled').show();
            $('#done_reordering').click(function () {

                /* Save the new ordering.
                 * ---------------------- */
                query_string = PortfolioEntry.Reorder.$list.sortable('serialize');

                $(this).text('Working...').attr('disabled','disabled');
                PortfolioEntry.Reorder.$done_reordering = $(this);

                var options = {
                    'type': 'POST',
                    'url': '/+do/save_portfolio_entry_ordering_do',
                    'data': query_string,
                    'success': function () {
                        PortfolioEntry.Reorder.$list.remove();
                        $('#portfolio_entries *').not('.loading_message').remove();
                        PortfolioEntry.Reorder.$hideUsWhenSorting.show();
                        $('#done_reordering').hide();
                        $('#projects_heading span:eq(0)').text('Projects');
                        $('a#reorder_projects').show();
                        $('#portfolio_entries .loading_message').show();
                        askServerForPortfolio();
                    },
                    'error': function () {
                        alert('Shit, there was an error saving your ordering.');
                    },
                };
                $.ajax(options);

            });
            
            return false;
        });
    }
}

$(PortfolioEntry.Reorder.init);

$.fn.getHandler = function(handler) {
    var real_obj = this[0];
    var handler_meta_array = $.data(real_obj, "events");
    for (var key in handler_meta_array) {
        if (key == handler) {
            return handler_meta_array[key];
        }
    }
    return false;
}


SaveAllButton = {};
SaveAllButton.updateDisplay = function () {
    $saveAllButton = $('button#save_all_projects');
    if ($('#portfolio .portfolio_entry:visible').size() === 0) {
        $saveAllButton.hide();
    }
    else {
        $saveAllButton.show();
    }
    if (SaveAllButton.getAllProjects().size() === 0) {
        $saveAllButton.attr('disabled', 'disabled');
    }
    else {
        $saveAllButton.removeAttr('disabled');
    }
    if (!$saveAllButton.getHandler('click')) {
        $saveAllButton.click(SaveAllButton.saveAll);
    }
};
SaveAllButton.getAllProjects = function() {
    return $('#portfolio .portfolio_entry.unsaved, #portfolio .portfolio_entry.unpublished');
    };
SaveAllButton.saveAll = function() {
    SaveAllButton.getAllProjects().each(function () {
            $(this).find('.publish_portfolio_entry:visible a').trigger('click');
    });
};

AutoSaucepan = {
    'init': function () {
        // This query string prefix triggers the automatic saucepan
        qs_pref = /^\?add_project_name=/;
        if (location.search.match(qs_pref) === null) return;

        // Check in the query string if there is anything
        var project_name = decodeURIComponent(location.search.replace(qs_pref,''));

        if (project_name) {
            // If so, simulate a click
            PortfolioEntry.Add.clickHandler(project_name);
        }
    }
};

$(function () {
        $('#importer .howto h5 a').click(function() {
            var $imp = $('#importer');
            $imp.toggleClass('expanded');
            return false;
            });
        });
}
// vim: set nu:
