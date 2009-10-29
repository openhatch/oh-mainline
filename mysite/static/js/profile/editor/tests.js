$.fn.assertOne = function(humanName) {
    if (typeof prefix == 'undefined') { prefix = ""; }
    fireunit.ok(this.size() == 1, prefix + "there's only one " + humanName);
    return this;
};

testProgressBarInvisibleOnPageLoad = function() {
    $('#importer #progressbar:visible').assertN('', 0);
};
$(testProgressBarInvisibleOnPageLoad);

testImportJGrowl = function() {
    fireunit.ok(typeof $.jGrowl != 'undefined', "jGrowl imported");
};
$(testImportJGrowl);

testBuildingBlocks = function() {
    var test = "testBuildingBlocks asserts: ";
    var blockSelectors = [
        '#portfolio_entry_building_block',
        '#citation_building_block',
        '#citation_form_building_block'
    ];
    for (var b = 0; b < blockSelectors.length; b++) {
        var blockSelector = blockSelectors[b];
        $block = $(blockSelector);
        fireunit.ok($block.size() == 1, test + blockSelector + " appears in document once.");
        fireunit.ok($block.filter(':hidden').size() == 1, test + blockSelector + " is hidden.");
    }
};
$(testBuildingBlocks);

message = 'We create PortfolioEntryElements when the event handler is responding to a list of objects from the server that includes a new PortfolioEntry.';
// FIXME: Come up with a suitable response, matching the description above.
mockedPortfolioResponse = {

    // DataImportAttempts
    'dias': [{'pk': 0}],

    // the progress of an import
    'import': {
        'running': false,
        'progress_percentage': 20
    },

    // Citations
    'citations': [
    {'pk': 0, 'fields': {'portfolio_entry': 0, 'is_published': 0}}, 
    {'pk': 1, 'fields': {'portfolio_entry': 0, 'is_published': 1}}, // These belong to different
    {'pk': 2, 'fields': {'portfolio_entry': 99, 'is_published': 1}}, // PortfolioEntries.
        // ^ This last one is never painted because there is no
        // corresponding pf entry.
    ],

    // Portfolio entries
    'portfolio_entries': [

    {
        'pk': 0, 'fields': {
            'project': 0,
            'project_description': 'described',
            'experience_description': 'i hacked things'
        }
    },

    {
        'pk': 1, 'fields': {
            'project': 1,
            'project_description': 'another project with a generic icon',
            'experience_description': 'i hacked things'
        }
    },

    ],

    // Projects
    'projects': [
    {
        'pk': 0,
        'fields': {
            'name': 'bindlestiff',
            'icon': 'images/icons/projects/0e9a1d7ab66f407fa9e2e3caf0eeda3d',
        }
    },
    {
        'pk': 1,
        'fields': {
            'name': 'a project with a generic icon',
            'icon': '',
        }
    },
    ],

    // Summaries
    'summaries': {
        '0': 'Ohloh repository index: Coded in shell script for 12 months as paulproteus since 2007.',
        '1': 'Summery'}
};

testUpdatePortfolio = function() {
    askServerForPortfolio(); // This will be mocked out when testJS = true
    $(mockedPortfolioResponse.portfolio_entries.slice(0,1)).each( function() {

            var portfolio_entry = this;

            // "this" is a JSON representation of a PortfolioEntry.
            // Did we create this PortfolioEntryElement?
            var pee = $("#portfolio_entry_" + portfolio_entry.pk);

            fireunit.ok( pee.size() == 1,
                "Expected a portfolio_entry corresponding to " + portfolio_entry);
            fireunit.ok( $('.project_name', pee).text() == "bindlestiff",
                "Expected the new portfolio_entry to say its project name is bindlestiff");
            fireunit.ok( pee.find("img.project_icon").attr('src') == 
                "/static/images/icons/projects/0e9a1d7ab66f407fa9e2e3caf0eeda3d",
                "Expected the project icon URL to properly be set.");
            fireunit.ok( $(".project_description", pee).text() == "described",
                "Expected the new portfolio_entry to say " +
                "its project description is 'described'");
            fireunit.ok( $(".experience_description", pee).text() == "i hacked things",
                "Expected the new portfolio_entry to say a description of the experience");

            /* 
             * Check that each citation in the response is also in the DOM.
             */

            // List the citations in the DOM.
            var dom_citations = $('.citations > li', pee);

            fireunit.ok(
                    dom_citations.size() == 2,
                    "Expected the number of citation elements in the " + 
                    "PortfolioEntryElement == 2 == the number of " +
                    "citations in the input that belong to this PEE. Instead " +
                    "the number of citation elements == " + dom_citations.size());

            // For each citation in the response, check that its data
            // is stuffed into the DOM.
            // I'll refer to a "citation in the response" as a
            // "response citation" from now on.
            var testThatResponseCitationHasADOMCitation = function() {
                var responseCitation = this;

                var msg = "Find DOM citation matching this response citation.";
                var $domCitation = $('#citation_'+responseCitation.pk);
                fireunit.ok($domCitation.size() > 0, msg);

                var msg = "Assert match of citation summary.";
                fireunit.ok($domCitation.find('.summary').text() == 
                        mockedPortfolioResponse.summaries[responseCitation.pk], 
                        msg);

                var msg = "Assert cssClass = is_published ? 'published' : 'unpublished'";
                if (responseCitation.fields.is_published == '1') {
                    fireunit.ok( ! $domCitation.hasClass('unpublished'), msg);
                }
                else {
                    fireunit.ok($domCitation.hasClass('unpublished'), msg);
                }
            };

            // Test that each of this portfolio entry's citations
            // has a corresponding DOM citation.
            $(mockedPortfolioResponse.citations.slice(0,2)).each(
                    testThatResponseCitationHasADOMCitation);

            // And now check the reverse: For each citation in the DOM,
            // check that its data is in the response.

            fireunit.ok($('.citations > li').size() == 2,
                    "Expected just one citation in the DOM.");
            fireunit.ok($('.citations > li')[0].id == 'citation_0', 
                    "Expected the first citation in the DOM to have id citation_0");
            fireunit.ok($('.citations > li')[1].id == 'citation_1', 
                    "Expected the second citation in the DOM to have id citation_1");

    });
};

$(testUpdatePortfolio);

testNoDuplication = function() {
    // Don't create duplicate citations or portfolio entries.
    // Clear the deck.
    $('#portfolio_entries *').remove();

    askServerForPortfolio();
    fireunit.ok($('.citations > li').size() == 2,
            "Assert there are two citations.");
    fireunit.ok($('.portfolio_entry:visible').size() == 2,
            "Assert there are two portfolio entries.");

    askServerForPortfolio();
    fireunit.ok($('.citations > li').size() == 2,
            "Assert there are still two citations.");
    fireunit.ok($('.portfolio_entry:visible').size() == 2,
            "Assert there are still two portfolio entries.");
};
$(testNoDuplication);

test = function() {
    // Clear the deck.
    $('#portfolio_entries *').remove();
    var prefix = 'button deletes citation: ';

    askServerForPortfolio();

    // Click the delete button for a citation.
    var citationID = 0;
    var $deleteLink = Citation.$getDeleteLink(citationID);
    $deleteLink.trigger('click');

    var citationElementID = '#citation_'+citationID;
    fireunit.ok($(citationElementID).size() == 1,
            prefix + "there's a citation with id " + citationElementID);
    fireunit.ok($(citationElementID+'.deleted').size() == 1,
            prefix + "there's a DELETED citation with id " + citationElementID);

    // Let's pretend the server said there was an error in deleting the citation.
    deleteCitationErrorCallback();
    // There should be a notifier shortly. Delay the notifier check, because
    // the notifier might take a moment to show up.
    var checkNotifierInAMoment = function () {
        var notifier = $('.jGrowl-notification .message');
        console.info(notifier);
        fireunit.ok(notifier.size() > 0,
                prefix + "there's at least one notifier.");
        var message = $('.jGrowl-notification .message').eq(0).text();
        console.log('notifier message: ', message);
        fireunit.ok(message.match(/error.*delete a citation/) != null,
                prefix + "notifier message matches /error.*delete a citation/");
    }
    window.setTimeout(checkNotifierInAMoment, 500);
};
$(test);

test = function() {
    $('#portfolio_entries *').remove();
    var prefix = 'button draws citation form: ';

    askServerForPortfolio();

    // Click the first 'Add another record' button. 
    var $button = $('.citations-wrapper .add').eq(0);
    $button.trigger('click');

    var $form = $button.closest('.citations-wrapper').find('.citation-forms li form.add_a_record');

    fireunit.ok($form.size() == 1, prefix + "the 'Add another record' button causes "
            + "exactly one form to appear in citation-forms.");
    var names = ['form_container_element_id', 'portfolio_entry', 'url'];
    for (var i = 0; i < names.length; i++) {
        var name = names[i];
        fireunit.ok($form.find('[name="'+name+'"]').size() == 1,
                prefix + "form has a field called" + name);
    }

};
$(test);

askServerForPortfolio_wasCalled = false;

test = function () {
    var prefix = "add a new citation: ";
    $add_a_new_citation_form = $('.citation-forms li:eq(0) form');
    $add_a_new_citation_form.find('[name="url"]').val('http://google.ca/');
    $add_a_new_citation_form.trigger('submit');
    fireunit.ok(true,
            prefix + "Yay, the page has not reloaded synchronously since adding a new citation.");
};
$(test);

test = function () {
    var prefix = "submission of a new citation: ";
    $form_container = $('.citation-forms li:eq(0)');
    fireunit.ok($form_container.size() == 1,
            prefix + "there's a form container eq(0)");
    var response = {
        'form_container_element_id': $form_container.attr('id')
    };
    handleServerResponseToNewRecordSubmission(response);
    fireunit.ok($('#'+response.form_container_element_id).size() == 0,
            prefix + "the form container has disappeared after we handle "
            + "the server's response to the successful submission of the form therein.");
};
$(test);

test = function () {
    var prefix = "show icon flagger only for nongeneric icons: ";
    fireunit.ok($('.portfolio_entry').eq(0).find('.icon_flagger').size() == 1,
            prefix + "assert project with nongeneric icon bears the link "
            + "'Flag icon as incorrect'"
            );
    fireunit.ok($('.portfolio_entry').eq(1).find('.icon_flagger').size() == 0,
            prefix + "assert project with generic icon doesn't bear the link "
            + "'Flag icon as incorrect'"
            );
};
$(test);

test = function () {
    var prefix = "flag icon as incorrect: ";
    // click a 'Flag icon as incorrect' link
    $icon_flagger = $('.icon_flagger').eq(0);
    fireunit.ok($icon_flagger.find('a').size() == 1,
            prefix + "expect link to exist before clicked.");

    // Mock post
    var post_copy = FlagIcon.post;
    FlagIcon.post = function () {
        FlagIcon.postOptions.success({
            'success': true,
                'portfolio_entry__pk': 0,
        });
    }
    $icon_flagger.find('a').trigger('click');
    fireunit.ok($icon_flagger.find('a').size() == 0,
            prefix + "expect link to be removed.'");
    fireunit.ok($icon_flagger.text().match(/default icon/),
            "expect link to be replaced with text including the phrase 'default icon'");
    $icon = $icon_flagger.closest('.portfolio_entry').find('img.project_icon');
    fireunit.ok($icon.size() == 1,
            prefix + "expect there to be an icon");
    fireunit.ok($icon.attr('src') == '/static/no-project-icon.png',
            "expect icon src to be (HARDCODED) /static/no-project-icon.png");

    FlagIcon.post = post_copy;
};
$(test);

test = function(params) {
    var mock = params.mock;
    console.log('mock', mock);

    var prefix = "test of PortfolioEntry.Save: ";

    if (!mock) { prefix = "integration " + prefix; }

    $pfEntry = $('.portfolio_entry:eq(0)');
    fireunit.ok(
            $pfEntry.size() == 1,
            prefix + "there's at least one pf entry on the page");

    $publishLink = $pfEntry.find('a.publish');
    fireunit.ok(
            $publishLink.size() == 1,
            prefix + "there's a publish link on the first pf entry");

    $projectDescriptionField = $pfEntry.find('textarea.project_description')
    fireunit.ok(
            $projectDescriptionField.size() == 1,
            prefix + "there's a textarea selectable by .project_description "
            + "on the first portfolio entry");

    $experienceDescriptionField = $pfEntry.find('textarea.experience_description')
    fireunit.ok(
            $experienceDescriptionField.size() == 1,
            prefix + "there's a textarea selectable by .experience_escription "
            + "on the first portfolio entry");

    fireunit.ok(
            $pfEntry.find('.citations li.unpublished').size() > 0,
            prefix + "(precondition) there's at least one unpublished citation in this pf entry.");

    // Edit textareas 
    $projectDescriptionField.val('new project description');
    $experienceDescriptionField.val('new experience description');

    if (mock) {

        // Test just the UI.
        
        // Mock out post to server for saving a PortfolioEntry.
        var post_copy = PortfolioEntry.Save.post;
        PortfolioEntry.Save.post = function() {
            // Check that the data in the post are correct.
            var data = PortfolioEntry.Save.postOptions.data;
            fireunit.ok(
                    data.project_description == 'new project description',
                    prefix + "project_description in post matches textarea");
            fireunit.ok(
                    data.experience_description == 'new experience description',
                    prefix + "experience_description in post matches textarea");
            
            // Don't actually post; instead, just handle a fake response object.
            var fakeResponse = {
                'portfolio_entry__pk': $pfEntry.attr('portfolio_entry__pk')
            };
            PortfolioEntry.Save.postOptions.success(fakeResponse);

            checkNotifiersForText('Portfolio entry saved');

        };

        $publishLink.trigger('click');

        // Reset mocking
        PortfolioEntry.Save.post = post_copy;
    }
    else {

        // Integration test.

        $publishLink.trigger('click');

        checkNotifiersForText('Portfolio entry saved');

        fireunit.ok(
                $pfEntry.find('.citations li.unpublished').size() == 0,
                prefix + "there are no unpublished citations in this pf entry.");

        function refreshAndCheckTextareas() {
            askServerForPortfolio();

            // Check that the textareas are populated correctly.
            fireunit.ok(
                    $pfEntry.find('.project_description').val() == 'new project description',
                    prefix + "project_description in post matches textarea");
            fireunit.ok(
                    $pfEntry.find('.experience_description').val() == 'new experience description',
                    prefix + "experience_description in post matches textarea");
        }


        refreshAndCheckTextareas();

        // Now do it again, but ruder.
        // Edit textareas, but *don't* click on the save button.
        $projectDescriptionField.val('unsaved project description');
        $experienceDescriptionField.val('unsaved experience description');

        // Ensure the new values have been overwritten.
        refreshAndCheckTextareas();
    }

    PortfolioEntry.Save.postOptions.error({});
    checkNotifiersForText('error saving this entry');

};
testUI = function() {
    test({mock: true}); // test just the UI
};
$(testUI);

// This should work if we test it for a PortfolioEntry that exists in the DB.

testIntegration = function() {
    test({mock: false}); // integration test
}
//$(testIntegration);

function checkNotifiersForText(text) {
    var checkNotifiersInAMoment = function () {
        var $allNotifiers = $('.jGrowl-notification .message');
        var messagesTogether = $allNotifiers.text(); // join the text of all the messages
        console.log(messagesTogether);
        fireunit.ok(messagesTogether.match(text) != null,
                "one of the notifier messages includes the phrase '" + text + "'");
    }
    window.setTimeout(checkNotifiersInAMoment, 1000); // Doesn't seem to work when <= 500.
}

/* Unit-test the deletion of portfolio entries */
testDeletePortfolioEntry = function(params) {
    var prefix = "test of PortfolioEntry.Delete: ";

    /* Reset the portfolio DOM objects */
    $('#portfolio_entries *').remove();
    askServerForPortfolio();

    /* Verify that there is a Portfolio Entry represented on the page
     * and that it has a delete link
     */
    $pfEntry = $('.portfolio_entry:eq(0)');
    fireunit.ok(
            $pfEntry.size() == 1,
            prefix + "there's at least one pf entry on the page");

    $deleteLink = $pfEntry.find('a.delete');
    fireunit.ok(
            $deleteLink.size() == 1,
            prefix + "there's a delete link on the first pf entry");

    fireunit.ok(
            $pfEntry.find('.citations li.unpublished').size() > 0,
            prefix + "(precondition) there's at least one unpublished citation in this pf entry.");

    // Test just the UI.
    
    // Mock out post to server for deleting a PortfolioEntry.
    var post_copy = PortfolioEntry.Delete.post;
    PortfolioEntry.Delete.post = function() {
	// Check that the data in the post are correct.
	var data = PortfolioEntry.Delete.postOptions.data;
	fireunit.ok(data.portfolio_entry__pk == '0', /* This is all we submit */
		    prefix + "Expected us to submit the primary key of the p_e we want to delete."); 
	// Don't actually post; instead, just handle a fake response object.
	var fakeResponse = {
        'success': true,
	    'portfolio_entry__pk': $pfEntry.attr('portfolio_entry__pk')
	};
	PortfolioEntry.Delete.postOptions.success(fakeResponse);

	/* Verify that the $pfEntry is now hidden */
	fireunit.ok($pfEntry.is(':hidden'), 
		    prefix + 'Expected pfEntry to disappear.');
    };
    
    $deleteLink.trigger('click');
    
    // Reset patching
    PortfolioEntry.Delete.post = post_copy;
};

$(testDeletePortfolioEntry);

testCitationHowTo = function() {
    var prefix = "citation howto: ";
    $('#portfolio_entries *').remove();
    askServerForPortfolio();
    $howtos = $('#portfolio_entries .citations-wrapper .howto');
    fireunit.ok($howtos.size() > 0, prefix + "Some howtos appear on the page.");

    $firstHowtoHideLink = $howtos.eq(0).find('a.hide_me');
    fireunit.ok($firstHowtoHideLink.size() == 1, prefix + "there is at least one howto hide link.");
    $firstHowtoHideLink.trigger('click');

    fireunit.ok($howtos.filter(':visible').size() == 0, prefix + "No howtos are visible after hide link clicked");
    for (var i = 0; i < $howtos.size(); i++) {
        $howto = $howtos.eq(i);
        console.info($howto);
        $showMeLink = $howto.closest('.citations-wrapper').find('a.show_howto:visible').assertOne('hidden show_howto link for this howto');
        console.info("showMeLink", $showMeLink);
        $showMeLink.trigger('click');
        fireunit.ok($howto.is(':visible'), prefix + "how to is visible after showme clicked.");
        fireunit.ok($showMeLink.is(':hidden'), prefix + "show me link is hidden after being clicked.");
        console.log("howtos size", $howtos.size());
    }

};
$(testCitationHowTo);

testImporterInputs = function() {
    var prefix = "importer inputs: ";
    $inputs = $('#importer input:text').assertN(prefix, 2);
};
$(testImporterInputs);

$.fn.assertN = function(prefix, n) {
    fireunit.ok(this.size() == n, prefix + "there are " + n + " elements matching " + this.selector);
    return this;
};

testProgressBar = function() {
    var prefix = "progress bar: ";

    // update portfolio, the mocked response will say no import is running.
    updatePortfolio(mockedPortfolioResponse);
    $bar = $('#importer #progressbar:visible');
    $bar.assertN(prefix, 0);

    // now make the mockedPortfolioResponse will say an import is running
    mockedPortfolioResponse.import.running = true;
    updatePortfolio(mockedPortfolioResponse);
    $bar = $('#importer #progressbar:visible');

    // a progress bar should now appear
    $bar.assertN(prefix, 1);

    fireunit.ok($bar.progressbar('option', 'value') == 20, prefix + "progressbar's value is 20");
};
$(testProgressBar);
// vim: set nu:
