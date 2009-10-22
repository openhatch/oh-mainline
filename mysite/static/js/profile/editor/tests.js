message = 'We create PortfolioEntryElements when the event handler is responding to a list of objects from the server that includes a new PortfolioEntry.';
// FIXME: Come up with a suitable response, matching the description above.
response = {
    // FIXME: We might not need these models here.
    'dias': [{'pk': 0}],

    'citations': [
    {'pk': 0, 'fields': {'portfolio_entry_id': 0}}, // These belong to different
    {'pk': 1, 'fields': {'portfolio_entry_id': 1}}, // PortfolioEntries.
    ],

    'portfolio_entries': [{'pk': 0, 'fields': {
        'project_id': 0,
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
                "/static/images/the-logo-bluegreen-125px.png",
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

            fireunit.ok($('.citations > li').size() == 1, "Expected just one citation in the DOM.");
            fireunit.ok($('.citations > li')[0].id == 'citation_0', 
                    "Expected the one citation in the DOM to have id citation_0");

    });
};

testUpdatePortfolio();

testNoDuplication = function() {
    $('#portfolio *').remove();

    updatePortfolio(response);
    fireunit.ok($('.citations > li').size() == 1, "Assert there's one citation.");
    fireunit.ok($('.portfolio_entry:visible').size() == 1, "Assert there's one portfolio entry.");

    updatePortfolio(response);
    fireunit.ok($('.citations > li').size() == 1, "Assert there's still one citation.");
    fireunit.ok($('.portfolio_entry:visible').size() == 1, "Assert there's still one portfolio entry.");
};
testNoDuplication();
