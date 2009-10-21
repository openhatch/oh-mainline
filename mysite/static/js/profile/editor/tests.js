message = 'We create PortfolioEntryElements when the event handler is responding to a list of objects from the server that includes a new PortfolioEntry.';
// FIXME: Come up with a suitable response, matching the description above.
response = {
    // FIXME: We might not need these models here.
    'dias': [{'pk': 0}],
    'citations': [{'pk': 0, 'fields': {'portfolio_entry_id': 0}}],
    'portfolio_entries': [{'pk': 0, 'fields': {'project_id': 0}}],
    'projects': [{'pk': 0, 'fields': {'name': 'bindlestiff'}}],
    'summaries': {'0': 'garglefoot'}
};

test = function() {
    updatePortfolio(response);
    $(response['portfolio_entries']).each( function() {
            // "this" is a JSON representation of a PortfolioEntry.
            // Did we create this PortfolioEntryElement?
            fireunit.ok(
                $('#portfolio_entry_element_' + this.pk).size()==1,
                "Expected a portfolio_entry_element corresponding to " + this);
    });
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
};

test();