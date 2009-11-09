if (typeof QUnit == 'undefined') {
    console.log('QUnit not imported.');
}

QUnitRunner = {};
QUnitRunner.ok = function(bool, message) {
    var bool = !!bool;
    if (typeof prefix == 'undefined') { var prefix = ""; }
    test(prefix, function() { ok(bool, message); });
};
QUnitRunner.compare = function(a, b, message) {
    if (typeof prefix == 'undefined') { prefix = ""; }
    test(prefix, function() { equals(a, b, message); });
};
QUnitRunner.testDone = function() {};

StupidRunner = {};
StupidRunner.ok = function(bool, message) {
    var bool = !!bool;
    if (!bool) { alert("Failed:" + message); }
};
StupidRunner.compare = function(a, b, message) {
    if (a !== b) { alert("Failed: " + a + " != " + b + "; " + message); }
};
StupidRunner.testDone = function() {};

// Pick a test runner here
tester = fireunit;
//tester = QUnitRunner;
//tester = StupidRunner;

$.fn.smartTrigger = function(handlerName) {
    tester.ok(this.getHandler(handlerName), "the thing has expected handler");
    this.trigger(handlerName);
};

$.fn.assertN = function(n) {
    if (typeof prefix == 'undefined') { prefix = ""; }
    tester.compare(n, this.size(), prefix + "expected there are " + n + " elements matching " + this.selector);
    return this;
};

$.fn.assertOne = function(humanName) {
    if (typeof prefix == 'undefined') { prefix = ""; }
    tester.ok(this.size() == 1, prefix + "there's only one " + humanName);
    return this;
};

/* Provide a helper for resetting the portfolio entries' state */
function redrawPortfolioEntries() {
    $('#portfolio_entries *').remove();
    askServerForPortfolio();    
}

testProgressBarInvisibleOnPageLoad = function() {
    $('#importer #progressbar:visible').assertN(0);
};
$(testProgressBarInvisibleOnPageLoad);

testImportJGrowl = function() {
    tester.ok(typeof $.jGrowl != 'undefined', "jGrowl imported");
};
$(testImportJGrowl);

testBuildingBlocks = function() {
    var prefix = "testBuildingBlocks asserts: ";
    var blockSelectors = [
        '#portfolio_entry_building_block',
        '#citation_building_block',
        '#citation_form_building_block'
            ];
    for (var b = 0; b < blockSelectors.length; b++) {
        var blockSelector = blockSelectors[b];
        $block = $(blockSelector);
        tester.ok($block.size() == 1, prefix + blockSelector + " appears in document once.");
        tester.ok($block.filter(':hidden').size() == 1, prefix + blockSelector + " is hidden.");
    }
};
$(testBuildingBlocks);

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
            'experience_description': 'i hacked things',
            'is_published': true,
        }
    },

    {
        'pk': 1, 'fields': {
            'project': 1,
            'project_description': 'another project with a generic icon',
            'experience_description': 'i hacked things',
            'is_published': false,
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

            // "this" is a JSON representation of a PortfolioEntry.
            var portfolio_entry = this;

            // Did we create this PortfolioEntryElement?
            var pee = $("#portfolio_entry_" + portfolio_entry.pk);

            tester.compare( pee.size(), 1,
                "Expected a portfolio_entry corresponding to " + portfolio_entry);
            tester.ok( $('.project_name', pee).text() == "bindlestiff",
                "Expected the new portfolio_entry to say its project name is bindlestiff");
            tester.ok( pee.find("img.project_icon").attr('src') == 
                "/static/images/icons/projects/0e9a1d7ab66f407fa9e2e3caf0eeda3d",
                "Expected the project icon URL to properly be set.");
            tester.ok( $(".project_description", pee).text() == "described",
                "Expected the new portfolio_entry to say " +
                "its project description is 'described'");
            tester.ok( $(".experience_description", pee).text() == "i hacked things",
                "Expected the new portfolio_entry to say a description of the experience");

            /* 
             * Check that each citation in the response is also in the DOM.
             */

            // List the citations in the DOM.
            var dom_citations = $('.citations > li', pee);

            tester.ok(
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
                tester.ok($domCitation.size() > 0, msg);

                var msg = "Assert match of citation summary HTML.";
                tester.compare($domCitation.find('.summary').html(),
                        mockedPortfolioResponse.summaries[responseCitation.pk], 
                        msg);

                var msg = "Assert cssClass = is_published ? 'published' : 'unpublished'";
                if (responseCitation.fields.is_published == '1') {
                    tester.ok( ! $domCitation.hasClass('unpublished'), msg);
                }
                else {
                    tester.ok($domCitation.hasClass('unpublished'), msg);
                }
            };

            // Test that each of this portfolio entry's citations
            // has a corresponding DOM citation.
            $(mockedPortfolioResponse.citations.slice(0,2)).each(
                    testThatResponseCitationHasADOMCitation);

            // And now check the reverse: For each citation in the DOM,
            // check that its data is in the response.

            tester.ok($('.citations > li').size() == 2,
                    "Expected just one citation in the DOM.");
            tester.ok($('.citations > li')[0].id == 'citation_0', 
                    "Expected the first citation in the DOM to have id citation_0");
            tester.ok($('.citations > li')[1].id == 'citation_1', 
                    "Expected the second citation in the DOM to have id citation_1");

    });
};

$(testUpdatePortfolio);


testNoDuplication = function() {
    // Don't create duplicate citations or portfolio entries.
    // Clear the deck.
    redrawPortfolioEntries();

    tester.compare($('.citations > li').size(), 2,
            "Assert there are two citations.");
    tester.compare($('.portfolio_entry:visible').size(), 2,
            "Assert there are two portfolio entries.");

    askServerForPortfolio();
    tester.compare($('.citations > li').size(), 2,
            "Assert there are still two citations.");
    tester.compare($('.portfolio_entry:visible').size(), 2,
            "Assert there are still two portfolio entries.");
};
$(testNoDuplication);

testCitationDelete = function() {
    // Clear the deck.
    $('#portfolio_entries *').remove();
    var prefix = 'button deletes citation: ';

    askServerForPortfolio();

    // Click the delete button for a citation.
    var citationID = 0;
    var $deleteLink = Citation.$getDeleteLink(citationID);
    $deleteLink.trigger('click');

    var citationElementID = '#citation_'+citationID;
    tester.ok($(citationElementID).size() == 1,
            prefix + "there's a citation with id " + citationElementID);
    tester.ok($(citationElementID+'.deleted').size() == 1,
            prefix + "there's a DELETED citation with id " + citationElementID);

    // Let's pretend the server said there was an error in deleting the citation.
    deleteCitationErrorCallback();
    
    checkNotifiersForText("delete a citation");
};
$(testCitationDelete);

testCitationFormCreate = function() {
    $('#portfolio_entries *').remove();
    var prefix = 'button draws citation form: ';

    askServerForPortfolio();

    // Click the first 'Add another record' button. 
    var $button = $('.citations-wrapper .add').eq(0);
    $button.trigger('click');

    var $form = $button.closest('.citations-wrapper').find('.citation-forms li form.add_a_record');

    tester.ok($form.size() == 1, prefix + "the 'Add another record' button causes "
            + "exactly one form to appear in citation-forms.");
    var names = ['form_container_element_id', 'portfolio_entry', 'url'];
    for (var i = 0; i < names.length; i++) {
        var name = names[i];
        tester.ok($form.find('[name="'+name+'"]').size() == 1,
                prefix + "form has a field called" + name);
    }

};
$(testCitationFormCreate);

askServerForPortfolio_wasCalled = false;

testCitationAdd = function () {
    var prefix = "add a new citation: ";
    $add_a_new_citation_form = $('.citation-forms li:eq(0) form');
    $add_a_new_citation_form.find('[name="url"]').val('http://google.ca/');
    $add_a_new_citation_form.trigger('submit');
    tester.ok(true,
            prefix + "Yay, the page has not reloaded synchronously since adding a new citation.");
};
$(testCitationAdd);

testCitationSubmit = function () {
    var prefix = "submission of a new citation: ";
    $form_container = $('.citation-forms li:eq(0)');
    tester.ok($form_container.size() == 1,
            prefix + "there's a form container eq(0)");
    var response = {
        'form_container_element_id': $form_container.attr('id')
    };
    handleServerResponseToNewRecordSubmission(response);
    tester.ok($('#'+response.form_container_element_id).size() == 0,
            prefix + "the form container has disappeared after we handle "
            + "the server's response to the successful submission of the form therein.");
};
$(testCitationSubmit);

testFlagIconOnly4Nongenerics = function () {
    var prefix = "show icon flagger only for nongeneric icons: ";
    tester.ok($('.portfolio_entry').eq(0).find('.icon_flagger').size() == 1,
            prefix + "assert project with nongeneric icon bears the link "
            + "'Flag icon as incorrect'"
            );
    tester.ok($('.portfolio_entry').eq(1).find('.icon_flagger:visible').size() == 0,
            prefix + "assert project with generic icon doesn't bear the link "
            + "'Flag icon as incorrect'"
            );
};
$(testFlagIconOnly4Nongenerics);

testFlagIcon = function () {
    var prefix = "flag icon as incorrect: ";
    // click a 'Flag icon as incorrect' link
    $icon_flagger = $('.icon_flagger').eq(0);
    tester.ok($icon_flagger.find('a').size() == 1,
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
    tester.ok($icon_flagger.find('a').size() == 0,
            prefix + "expect link to be removed.'");
    tester.ok(!!$icon_flagger.text().match(/default icon/),
            "expect link to be replaced with text including the phrase 'default icon'");
    $icon = $icon_flagger.closest('.portfolio_entry').find('img.project_icon');
    tester.ok($icon.size() == 1,
            prefix + "expect there to be an icon");
    tester.ok($icon.attr('src') == '/static/no-project-icon.png',
            "expect icon src to be (HARDCODED) /static/no-project-icon.png");

    FlagIcon.post = post_copy;
};
$(testFlagIcon);

function deepCopy(obj) {
    var copy = {};
    $.extend(true, copy, obj);
    return copy;
}

testPortfolioEntrySave = function(params) {

    $('#portfolio_entries *').remove();

    // set is_published in the first citation of the second portfolio entry to false.
    mockedPortfolioResponse2 = deepCopy(mockedPortfolioResponse);
    mockedPortfolioResponse2.portfolio_entries[0].fields.is_published = false;

    updatePortfolio(mockedPortfolioResponse2);

    var mock = params.mock;

    var prefix = "test of PortfolioEntry.Save: ";

    if (!mock) { prefix = "integration " + prefix; }

    $pfEntry = $('.portfolio_entry:eq(0)');
    tester.ok(
            $pfEntry.size() == 1,
            prefix + "there's at least one pf entry on the page");

    $saveAndPublishButton = $pfEntry.find('li.save_and_publish_button:visible a').assertN(1);

    $projectDescriptionField = $pfEntry.find('textarea.project_description')
        tester.ok(
                $projectDescriptionField.size() == 1,
                prefix + "there's a textarea selectable by .project_description "
                + "on the first portfolio entry");

    $experienceDescriptionField = $pfEntry.find('textarea.experience_description')
        tester.ok(
                $experienceDescriptionField.size() == 1,
                prefix + "there's a textarea selectable by .experience_escription "
                + "on the first portfolio entry");

    tester.ok(
            $pfEntry.find('.citations li.unpublished').size() > 0,
            prefix + "(precondition) there's at least one unpublished citation in this pf entry.");

    $projectDescriptionField.val('new project description');
    $experienceDescriptionField.val('new experience description');

    if (mock) {

        // Test just the UI.

        // Mock out post to server for saving a PortfolioEntry.
        var post_copy = PortfolioEntry.Save.post;
        PortfolioEntry.Save.post = function() {
            // Check that the data in the post are correct.
            var data = PortfolioEntry.Save.postOptions.data;
            tester.compare(
                    data.project_description, 'new project description',
                    prefix + "project_description in postOptions.data matches textarea");
            tester.compare(
                    data.experience_description,  'new experience description',
                    prefix + "experience_description in postOptions.data matches textarea");

            // Don't actually post; instead, just handle a fake response object.
            var fakeResponse = {
                'portfolio_entry__pk': $pfEntry.attr('portfolio_entry__pk')
            };
            PortfolioEntry.Save.postOptions.success(fakeResponse);
            
            checkNotifiersForText('Portfolio entry saved');

        };

        $saveAndPublishButton.trigger('click');

        tester.ok($pfEntry.hasClass('unpublished') == false, "$pfEntry.hasClass('unpublished')");

        // Reset mocking
        PortfolioEntry.Save.post = post_copy;
    }
    else {

        // Integration test.

        $saveAndPublishButton.trigger('click');

        checkNotifiersForText('Portfolio entry saved');

        tester.ok(
                $pfEntry.find('.citations li.unpublished').size() == 0,
                prefix + "there are no unpublished citations in this pf entry.");

        function refreshAndCheckTextareas() {
            askServerForPortfolio();

            // Check that the textareas are populated correctly.
            tester.ok(
                    $pfEntry.find('.project_description').val() == 'new project description',
                    prefix + "project_description in post matches textarea");
            tester.ok(
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
    testPortfolioEntrySave({mock: true}); // test just the UI
};
$(testUI);

// This should work if we test it for a PortfolioEntry that exists in the DB.

testIntegration = function() {
    testPortfolioEntrySave({mock: false}); // integration test
}
//$(testIntegration);

function checkNotifiersForText(text) {
    var checkNotifiersInAMoment = function () {
        var $allNotifiers = $('.jGrowl-notification .message');
        var messagesTogether = $allNotifiers.text(); // join the text of all the messages
        console.log(messagesTogether);
        tester.ok(messagesTogether.match(text) != null,
                "one of the notifier messages includes the phrase '" + text + "'");
    }
    window.setTimeout(checkNotifiersInAMoment, 3000); // Doesn't seem to work when <= 500.
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
    tester.ok(
            $pfEntry.size() == 1,
            prefix + "there's at least one pf entry on the page");

    $deleteLink = $pfEntry.find('li.delete_portfolio_entry a');
    tester.ok(
            $deleteLink.size() == 1,
            prefix + "there's a delete link on the first pf entry");

    tester.ok(
            $pfEntry.find('.citations li.unpublished').size() > 0,
            prefix + "(precondition) there's at least one unpublished citation in this pf entry.");

    // Test just the UI.

    // Mock out post to server for deleting a PortfolioEntry.
    var post_copy = PortfolioEntry.Delete.post;
    PortfolioEntry.Delete.post = function() {
        // Check that the data in the post are correct.
        var data = PortfolioEntry.Delete.postOptions.data;
        tester.ok(data.portfolio_entry__pk == '0', /* This is all we submit */
                prefix + "Expected us to submit the primary key of the p_e we want to delete."); 
        // Don't actually post; instead, just handle a fake response object.
        var fakeResponse = {
            'success': true,
            'portfolio_entry__pk': $pfEntry.attr('portfolio_entry__pk')
        };
        PortfolioEntry.Delete.postOptions.success(fakeResponse);

        tester.ok($pfEntry.is(':hidden'), 'Expected $pfEntry to disappear.');
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
    tester.ok($howtos.size() > 0, prefix + "Some howtos appear on the page.");

    $firstHowtoHideLink = $howtos.eq(0).find('a.hide_me');
    tester.ok($firstHowtoHideLink.size() == 1, prefix + "there is at least one howto hide link.");
    $firstHowtoHideLink.trigger('click');

    tester.ok($howtos.filter(':visible').size() == 0, prefix + "No howtos are visible after hide link clicked");
    for (var i = 0; i < $howtos.size(); i++) {
        $howto = $howtos.eq(i);
        console.info($howto);
        $showMeLink = $howto.closest('.citations-wrapper').find('a.show_howto:visible').assertOne('hidden show_howto link for this howto');
        console.info("showMeLink", $showMeLink);
        $showMeLink.trigger('click');
        tester.ok($howto.is(':visible'), prefix + "how to is visible after showme clicked.");
        tester.ok($showMeLink.is(':hidden'), prefix + "show me link is hidden after being clicked.");
        console.log("howtos size", $howtos.size());
    }

};
$(testCitationHowTo);

testImporterInputs = function() {
    var prefix = "importer inputs: ";
    $inputs = $('#importer input:text').assertN(2);
};
$(testImporterInputs);

testProgressBar = function() {
    var prefix = "progress bar: ";

    // update portfolio, the mocked response will say no import is running.
    updatePortfolio(mockedPortfolioResponse);
    $bar = $('#importer #progressbar:visible');
    $bar.assertN(0);

    // now make the mockedPortfolioResponse will say an import is running
    mockedPortfolioResponse.import.running = true;
    updatePortfolio(mockedPortfolioResponse);
    $bar = $('#importer #progressbar:visible');

    // a progress bar should now appear
    $bar.assertN(1);

    tester.ok($bar.progressbar('option', 'value') == 20, prefix + "progressbar's value is 20");
};
$(testProgressBar);

testUpdateExistingCitations = function() {
    var prefix = "the portfolio will update correctly in response to a citation being published: ";
    updatePortfolio(mockedPortfolioResponse);
    $firstCitation = $('.citations li').eq(0);
    tester.ok( $firstCitation.hasClass('unpublished'),
            prefix + "First citation has 'unpublished' class.");
    mockedPortfolioResponse.citations[0].fields.is_published = '1';
    updatePortfolio(mockedPortfolioResponse);
    tester.ok( $firstCitation.hasClass('unpublished') == false,
            prefix + "First citation now lacks 'unpublished' class.");
};
$(testUpdateExistingCitations);

testUIResponseToPFEntryPublication = function() {
    var prefix = "portfolio entry / save / ui response: ";

    redrawPortfolioEntries();

    // preconditions
    tester.ok(
            mockedPortfolioResponse.portfolio_entries[0].fields.is_published,
            prefix + "assert first pf entry in response is published");
    tester.ok(
            mockedPortfolioResponse.portfolio_entries[1].fields.is_published == false,
            prefix + "assert second pf entry in response is unpublished");
    $firstEntry = $('.portfolio_entry:eq(0)').assertN(1);
    $secondEntry = $('.portfolio_entry:eq(1)').assertN(1);

    // assertions
    tester.compare(
            $firstEntry.hasClass('unpublished'), false,
            prefix + "assert first pf entry in dom lacks class unpublished");
    $firstEntry.find('.portfolio_entry_is_published:visible').assertN(1);
    tester.ok(
            $secondEntry.hasClass('unpublished'),
            prefix + "assert second pf entry in dom has class unpublished");
};
$(testUIResponseToPFEntryPublication);

testLinkDrawsAWidgetForAddingAPortfolioEntry = function () {

    redrawPortfolioEntries();

    var prefix = "link draws a widget for adding a portfolio entry: ";

    $link = $('a#add_pf_entry').assertN(1);

    $widget = $('#portfolio_entries .portfolio_entry.adding');
    tester.compare( $widget.size(), 0, prefix + "there's no widget until we click");

    $link.trigger('click');

    $widget = $($widget.selector);
    tester.compare( $widget.size(), 1, prefix + "there's one widget after we click");

    tester.ok($widget.attr('id').match(/^element_/), prefix + "Adder widget has a unique ID.");

    // Before the widget has been saved/published, the 'Add another link' and howto are hidden.
    $widget.find('.citations:visible, .citation_forms:visible').assertN(0);
    // A placeholder is visible.
    $widget.find('.involvement_placeholder:visible').assertN(1);

    // make sure we have one
    $projectNameField = $widget.find('input:text.project_name').assertN(1);
    $projectDescriptionField = $widget.find('textarea.project_description').assertN(1);
    $experienceDescriptionField = $widget.find('textarea.experience_description').assertN(1);

    $projectNameField.val('new name');
    $projectDescriptionField.val('new project description');
    $experienceDescriptionField.val('new experience description');

    $saveLink = $widget.find('.publish_portfolio_entry:visible a').assertN(1);

    // Monkeypatch function that normally posts to server for saving/publishing a PortfolioEntry.
    var post_copy = PortfolioEntry.Save.post;
    PortfolioEntry.Save.post = function() {
        // Check that the data in the post are correct.
        var data = PortfolioEntry.Save.postOptions.data;
        tester.compare(
                data.pf_entry_element_id, $widget.attr('id'),
                prefix + "pf_entry_element_id in postOptions.data is the widget's ID");
        tester.compare(
                data.project_name, 'new name',
                prefix + "project_name in postOptions.data matches input field");
        tester.compare(
                data.project_description, 'new project description',
                prefix + "project_description in postOptions.data matches textarea");
        tester.compare(
                data.experience_description,  'new experience description',
                prefix + "experience_description in postOptions.data matches textarea");

        var new_pf_entry_pk = 99999; // In real life this will be a new pk.
        $('#portfolio_entry_'+new_pf_entry_pk).assertN(0); // Let's just make sure it isn't used
        // for some reason.

        // Don't actually post; instead, just handle a fake response object.
        var fakeResponse = {
            'pf_entry_element_id': $widget.attr('id'),
            'portfolio_entry__pk': new_pf_entry_pk
        };
        PortfolioEntry.Save.postOptions.success(fakeResponse);
        
        checkNotifiersForText('Portfolio entry saved');

        tester.compare($widget.attr('id'), 'portfolio_entry_'+new_pf_entry_pk,
                prefix + "Widget ID updated to reflect new primary key assigned to "
                + "corresponding record in the db.");
        tester.compare($widget.attr('portfolio_entry__pk'), ""+new_pf_entry_pk,
                prefix + "Widget attr portfolio_entry__pk updated to reflect new "
                + "primary key assigned to corresponding record in the db.");

    };

    // When this click handler is called it will end up using the function above, not the default.
    $saveLink.trigger('click');

    $recently_added_pf_entry = $widget; // Graduated now.

    $recently_added_pf_entry.find('input:text.project_name').assertN(0);

    tester.compare(
            $recently_added_pf_entry.find('span.project_name').assertN(1).text(),
            "new name",
            prefix + "Project name is a span containing the name."
            );

    tester.ok(
            ! $recently_added_pf_entry.hasClass('adding'),
            prefix + "Recently added pf entry no longer has class 'adding'."
            );

    // Reset monkeypatching
    PortfolioEntry.Save.post = post_copy;

};
$(testLinkDrawsAWidgetForAddingAPortfolioEntry);


// FIXME: Test: Add the 'unsaved' class to a pf entry when textfields are modified.
testAddUnsavedClassWhenTextfieldsAreModified = function() {
    redrawPortfolioEntries();
    var prefix = "test add unsaved class when textfields are modified: ";
                                                              // : " <-- little dude
                                                              // : "; <-- asheesh sees a dude here, i do not.
    $firstPublishedPFE = $('.portfolio_entry').not('.unpublished').eq(0);
    tester.compare($firstPublishedPFE.hasClass('unsaved'), false,
            prefix + "first published pf entry doesn't have class unsaved");
    tester.compare( $firstPublishedPFE.find('textarea').size(), 2,
            prefix + "assume first published pfe has just two textareas");
    $firstPublishedPFE.find('textarea:eq(0)').trigger('keydown');
    tester.ok($firstPublishedPFE.hasClass('unsaved'),
            prefix + "after we triggered keydown on the first textarea, first published pf entry "
            + "now has class unsaved");
    $firstPublishedPFE.removeClass('unsaved');
    $firstPublishedPFE.find('textarea:eq(1)').trigger('keydown');
    tester.ok($firstPublishedPFE.hasClass('unsaved'), 
            prefix + "after we triggered keydown on the second textarea, first published pf entry "
            + "now has class unsaved");
};
$(testAddUnsavedClassWhenTextfieldsAreModified);

testShowUserMessagesDuringImport = function() {
    var mockedPortfolioResponse2 = deepCopy(mockedPortfolioResponse);
    mockedPortfolioResponse2.messages = ['message!'];
    updatePortfolio(mockedPortfolioResponse2);
    checkNotifiersForText("message!");
};
$(testShowUserMessagesDuringImport);

testDeleteAdderWidget = function() {
    prefix = "delete adder widget: ";
    redrawPortfolioEntries();
    $('a#add_pf_entry').assertN(1).trigger('click');
    function momentarily() {
        $widget = $('#portfolio_entries .portfolio_entry.adding').assertN(1);
        $widget.find('.delete_portfolio_entry a').assertN(1).smartTrigger('click');
        $($widget.selector).assertN(0);
    }
    window.setTimeout(momentarily, 2000);
};
$(testDeleteAdderWidget);

$(function () {
        window.setTimeout("tester.testDone();", 5000);
        });

// vim: set nu ai:
