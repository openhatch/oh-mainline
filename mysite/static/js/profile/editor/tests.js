message = 'We create PortfolioEntryElements when the event handler is responding to a list of objects from the server that includes a new PortfolioEntry.';
// FIXME: Come up with a suitable response, matching the description above.
response = {
    // FIXME: We might not need these models here.
    'dias': [{'pk': 0}],
    'citations': [{'pk': 0, 'fields': {'portfolio_entry_id': 0}}],
    'portfolio_entries': [{'pk': 0, 'fields': {
        'project_id': 0,
        'project_description': 'described',
        'experience_description': 'i hacked things'
    }}],
    'projects': [{'pk': 0, 'fields': {'name': 'bindlestiff'}}],
    'summaries': {'0': 'garglefoot'}
};

test = function() {
    updatePortfolio(response);
    $(response['portfolio_entries']).each( function() {
            // "this" is a JSON representation of a PortfolioEntry.
            // Did we create this PortfolioEntryElement?
            var pee = $("#portfolio_entry_element_" + this.pk);

            fireunit.ok( pee.size() == 1,
                "Expected a portfolio_entry_element corresponding to " + this);
            fireunit.ok( $('.project_name', pee).text() == "bindlestiff",
                "Expected the new portfolio_entry_element to say its project name is bindlestiff");
            fireunit.ok( $(".project_description", pee).text() == "described",
                "Expected the new portfolio_entry_element to say " +
                "its project description is 'described'");
            fireunit.ok( $(".experience_description", pee).text() == "i hacked things",
                "Expected the new portfolio_entry_element to say a description of the experience");

            /* 
             * Check that each citation in the response is also in the DOM.
             */

            // List the citations in the DOM.
            var dom_citations = $('.citations li', pee);

            fireunit.ok(
                    dom_citations.size() == response.citations.length,
                    "Expected the number of citation elements in the " + 
                    "PortfolioEntryElement to be equal the number of " +
                    "citations in the input.");
            // The above test presumes that all the citations in the input
            // belong to this PortfolioEntry.

            /*
               for each object:
               if model=Citation:
               - try to find the CitationElement on the page
               - if exists, update the CitationElement with its (possibly) new values
               - if not, create it with class staging

               for each object:
               if model=DataImportAttempt:
               - update the progress bar
               $('staging').removeClass('staging');
               */
    });
};

test();
