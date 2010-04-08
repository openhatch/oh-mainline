$.fn.toggleText = function(text1, text2) {
    newtext = (this.text() == text2) ? text1 : text2;
    return this.text(newtext);
};

$.fn.toggleExpanded = function() {
    //console.log(this, 'toggleExpanded');
    this.toggleClass('expanded');
    return this;
};
// Return the available content height space in browser window

SearchResults = {}

SearchResults.bindEventHandlers = function () {

    console.log('SearchResults.bindEventHandlers');

    $('.project__name, .first-line').click(function () {
            $result = $(this.parentNode.parentNode);
            $result.toggleExpanded();
            // don't use this, so that links work return false;
            });

    $('.show-details').click(function () {
            $result = $(this.parentNode.parentNode.parentNode.parentNode);
            $result.toggleExpanded();
            return false;
            });

    $('#expand-all-link').click(function() {
            $('.gewgaws li').addClass('expanded');
            return false;
            });

    $('#collapse-all-link').click(function() {
            $('.gewgaws li').removeClass('expanded');
            return false;
            });

}

SearchResults.shortcutsEnabled = false;

SearchResults.moveSearchResultFocusDown = function () {
    SearchResults.lightSearchResult(SearchResults.getLitSearchResultIndex() + 1);
};

SearchResults.moveSearchResultFocusUp = function () {
    SearchResults.lightSearchResult(SearchResults.getLitSearchResultIndex() - 1);
};

SearchResults.initializeAutoComplete = function() {
    $input = $("#opps form input[type='text']");
    //console.log("input", $input);
    url = "/search/get_suggestions";
    acOptions = {
        'minChars': 1,
        /*
           'extraParams': {
           'partial_query': '',
           },*/
        'multiple': true,
        'multipleSeparator': " ",
        'matchContains': true
    };
    // $input.autocomplete(url, acOptions);
};


$(SearchResults.bindEventHandlers);

$(function() {
        SearchResults.lightSearchResult(0);
        });



/* vim: set ai ts=4 sts=4 et sw=4: */
