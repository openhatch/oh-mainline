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
response = {
    // FIXME: We might not need these models here.
    'dias': [{'pk': 0}],

    'citations': [
    {'pk': 0, 'fields': {'portfolio_entry': 0}}, // These belong to different
    {'pk': 1, 'fields': {'portfolio_entry': 1}}, // PortfolioEntries.
    ],

    'portfolio_entries': [{'pk': 0, 'fields': {
        'project': 0,
        'project_description': 'described',
        'experience_description': 'i hacked things'
    }
    }
    ],
    'projects': [{'pk': 0, 'fields': {'name': 'bindlestiff'}}],
    'summaries': {'0': 'Ohloh repository index: Coded in shell script for 12 months as paulproteus since 2007.'},
    'project_icon_urls': {'0': '/people/project_icon/Web%20Team%20projects/'}
};

testUpdatePortfolio = function() {
    updatePortfolio(response);
    $(response.portfolio_entries).each( function() {

            var portfolio_entry = this;

            // "this" is a JSON representation of a PortfolioEntry.
            // Did we create this PortfolioEntryElement?
            var pee = $("#portfolio_entry_" + portfolio_entry.pk);

            fireunit.ok( pee.size() == 1,
                "Expected a portfolio_entry corresponding to " + portfolio_entry);
            fireunit.ok( $('.project_name', pee).text() == "bindlestiff",
                "Expected the new portfolio_entry to say its project name is bindlestiff");
            fireunit.ok( pee.find("img.project_icon").attr('src') == 
                "/people/project_icon/Web%20Team%20projects/",
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
                    dom_citations.size() == 1,
                    "Expected the number of citation elements in the " + 
                    "PortfolioEntryElement == 1 == the number of " +
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
                        response.summaries[responseCitation.pk], 
                        msg);
            };

            // Test that each of this portfolio entry's citations
            // has a corresponding DOM citation.
            $([response.citations[0]]).each(testThatResponseCitationHasADOMCitation);

            // And now check the reverse: For each citation in the DOM,
            // check that its data is in the response.

            fireunit.ok($('.citations > li').size() == 1,
                    "Expected just one citation in the DOM.");
            fireunit.ok($('.citations > li')[0].id == 'citation_0', 
                    "Expected the one citation in the DOM to have id citation_0");

    });
};

$(testUpdatePortfolio);

testNoDuplication = function() {
    // Clear the deck.
    $('#portfolio *').remove();

    updatePortfolio(response);
    fireunit.ok($('.citations > li').size() == 1, "Assert there's one citation.");
    fireunit.ok($('.portfolio_entry:visible').size() == 1, "Assert there's one portfolio entry.");

    updatePortfolio(response);
    fireunit.ok($('.citations > li').size() == 1, "Assert there's still one citation.");
    fireunit.ok($('.portfolio_entry:visible').size() == 1, "Assert there's still one portfolio entry.");
};
$(testNoDuplication);

testDeleteCitation = function() {
    // Clear the deck.
    $('#portfolio *').remove();
    var test = 'testDeleteCitation asserts: ';

    updatePortfolio(response);

    // Click the delete button for a citation.
    var citationID = 0;
    var $deleteLink = Citation.$getDeleteLink(citationID);
    $deleteLink.trigger('click');

    var citationElementID = '#citation_'+citationID;
    fireunit.ok($(citationElementID).size() == 1,
            test + "there's a citation with id " + citationElementID);
    fireunit.ok($(citationElementID+'.deleted').size() == 1,
            test + "there's a DELETED citation with id " + citationElementID);

    // Let's pretend the server said there was an error in deleting the citation.
    deleteCitationErrorCallback();
    // There should be a notifier shortly. Delay the notifier check, because
    // the notifier might take a moment to show up.
    var checkNotifierInAMoment = function () {
        var notifier = $('.jGrowl-notification .message');
        console.info(notifier);
        fireunit.ok(notifier.size() > 0, test + "there's at least one notifier.");
        var message = $('.jGrowl-notification .message').eq(0).text();
        console.log('notifier message: ', message);
        fireunit.ok(message.match(/error.*delete a citation/) != null,
                test + "notifier message matches /error.*delete a citation/");
    }
    window.setTimeout(checkNotifierInAMoment, 500);
};
$(testDeleteCitation);

testAddARecordButtonDrawsAForm = function() {
    $('#portfolio *').remove();
    var test = 'testAddARecordButtonDrawsAForm asserts: ';

    updatePortfolio(response);

    // Click the first 'Add another record' button. 
    var $button = $('.citations-wrapper .add').eq(0);
    $button.trigger('click');

    var $form = $button.closest('.citations-wrapper').find('.citation-forms li form.add_a_record');

    fireunit.ok($form.size() == 1, test + "the 'Add another record' button causes "
            + "exactly one form to appear in citation-forms.");
    var names = ['form_container_element_id', 'portfolio_entry', 'url'];
    for (var i = 0; i < names.length; i++) {
        var name = names[i];
        fireunit.ok($form.find('[name="'+name+'"]').size() == 1,
                test + "form as a field called" + name);
    }

};
$(testAddARecordButtonDrawsAForm);

askServerForPortfolio_wasCalled = false;

prefix = "add a new citation: ";
test = function () {
    $add_a_new_citation_form = $('.citation-forms li:eq(0) form');
    $add_a_new_citation_form.find('[name="url"]').val('http://google.ca/');
    $add_a_new_citation_form.trigger('submit');
    fireunit.ok(true,
            prefix + "Yay, the page has not reloaded synchronously since adding a new citation.");
};
$(test);

// vim: set nu:
