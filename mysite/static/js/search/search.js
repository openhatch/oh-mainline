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

/* vim: set ai ts=4 sts=4 et sw=4: */
