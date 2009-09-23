$.fn.toggleText = function(text1, text2) {
    newtext = (this.text() == text2) ? text1 : text2;
    return this.text(newtext);
};

$.fn.toggleExpanded = function() {
    //console.log(this, 'toggleExpanded');
    this.toggleClass('expanded');
    this.scrollIntoView(); 
    return this;
};
// Return the available content height space in browser window

// FIXME: This doesn't handle a bottom scrollbar well.
$.viewportHeight = function() { var h = 0; if (typeof(window.innerHeight) == "number") { h = window.innerHeight; } else { if (document.documentElement && document.documentElement.clientHeight) { h = document.documentElement.clientHeight; } else { if (document.body && document.body.clientHeight) { h = document.body.clientHeight; } } } return h; }

$.fn.scrollIntoView = function() {
    elemTop = this.offset().top;
    elemBottom = elemTop + this.height();
    scrollTop = $(document).scrollTop();
    viewportHeight = $.viewportHeight();
    scrollBottom = scrollTop + viewportHeight;
    if (elemTop < scrollTop)  {
        $.scrollTo(this, 0, {offset: -5});
    }
    if (elemBottom > scrollBottom) {
        $.scrollTo(elemBottom - viewportHeight + 10);
    }
}


$(function() {

        //SearchResults.lightSearchResult(0);

        $('#expand-all-link').click(function() {
            $('.gewgaws li').addClass('expanded');
            return false;
            });

        $('#collapse-all-link').click(function() {
            $('.gewgaws li').removeClass('expanded');
            return false;
            });

        /*
        $(document).bind('keypress',
            {combi: '\\', disableInInput: true},
            SearchResults.focusSearchInput);

        $(document).bind('keyup',
            {combi: 'j', disableInInput: true},
            SearchResults.moveSearchResultFocusDown);

        $(document).bind('keyup',
                {combi: 'n', disableInInput: true},
                SearchResults.moveSearchResultFocusDown);

        $(document).bind('keyup',
                {combi: 'k', disableInInput: true},
                SearchResults.moveSearchResultFocusUp);

        $(document).bind('keyup',
                {combi: 'p', disableInInput: true},
                SearchResults.moveSearchResultFocusUp);

        $(document).bind('keyup',
                {combi: 'o', disableInInput: true}, 
                function() {
                $('.gewgaws .lit-up').toggleExpanded();
                });

        $('.first-line').hover(
                function() { $(this).addClass('hover'); },
                function() { $(this).removeClass('hover'); }
                );
                */

        /* FIXME: TEMPORARILY DISABLED. */
        /* Takes a query and updates the page. */
        /*
        $("#button").click(function() {
                // Put form values into an associative array.
                return SearchResults.update($('form').serializeArray());
                });
        */

        var pageLinkClickHandler = function() {
            /* Take the HREF and convert to wacky serializeArray,
             * send to update() */

            var fruitySerialized = new Array();

            var splittedOnAmpersands = this.href.split('?')[1].split('&');
            for (var index in splittedOnAmpersands) {
                var splitted = splittedOnAmpersands[index].split('=');    
                var key = decodeURIComponent(splitted[0]);
                var value = decodeURIComponent(splitted[1]);
                var fruity_pushable = {'name': key, 'value': value};
                /* update the thisstart and thisend globals */
                if (key == 'start') {
                    thisstart = parseInt(value);
                }
                if (key == 'end') {
                    thisend = parseInt(value);
                }
                fruitySerialized.push(fruity_pushable);
            }
            console.log('FRUITYSERIALIZED:');
            console.log(fruitySerialized);
            console.log('SLASH FRUITYSERIALIZED:');

            return false;
            // fixme: temporary
            // What kind of data structure does SearchResults.update expect?
            return SearchResults.update(fruitySerialized);
        };

        /* FIXME: TEMPORARILY DISABLED. */
        // $('#prev-page, #next-page').click(pageLinkClickHandler);

        // Handle autocomplete. {{{
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
        // }}}
});

SearchResults = {}

SearchResults.bindEventHandlers = function () {

        $('.title').click(function () {
                $result = $(this.parentNode.parentNode);
                $result.toggleExpanded();
                return false;
                });

        $('.show-details').click(function () {
                $result = $(this.parentNode.parentNode.parentNode);
                $result.toggleExpanded();
                return false;
                });

        $('.first-line a.title').click(function () {
                $result = $(this.parentNode.parentNode.parentNode);
                $result.toggleExpanded();
                return false;
                });
}

SearchResults.focusSearchInput = function () {
    //console.log('focus search input called');
    $("#opps form input[type='text']").focus();
};

SearchResults.queryURL = "/search/?";

SearchResults.$resultsDOMList = $('.gewgaws ul');

SearchResults.getLitSearchResultIndex = function() {
    // FIXME: Remember the index of the lit gewgaw in Javascript,
    // and avoid going through CSS.
    return $('.gewgaws li').index($('.lit-up')[0]);
};

SearchResults.fetchSearchResultsToDOM = function (queryString) {
    url = this.queryURL + queryString + "&jsoncallback=?";
    $.getJSON(url, this.jsonArrayToDocument);
    SearchResults.lightSearchResult(0);

    // Fix <https://openhatch.org/bugs/issue5>:
    // In opp search, keyboard shortcuts are not enabled immediately
    // because focus not on search results.
    // Tested by function: `SearchTests.blurSearchFieldWhenNewResultsAppear`.
    if (SearchResults.shortcutsEnabled) {
        console.debug("opps ul: ", $("#opps ul"));
        $("#opps ul a:first-child").focus();
    }

};

SearchResults.jsonArrayToDocument = function (jsonArray) {
    $('.gewgaws li').hide();

    // Create a results list if there's isn't one already.
    var noResultsList = $('#opps ul').size() == 0;
    if (noResultsList) { $("<ul>").appendTo('#opps'); }

    $('.search-result-control').show();

    var dataToDOM = function(i) {
        // Add data from JSON array element to DOM.
        $result = $(".gewgaws li").eq(i);

        // This function updates the result list.
        // It will attempt to recycle list items
        // that are already in the DOM.
        // However...
        if ( $result.size() == 0 ) {

            // Sometimes we run out of list items. 
            // E.g., when no list items were generated in the first place.
            // E.g., when the search query was an empty string,
            // and the Django template didn't print any results.

            // Remove any messages to the effect of "No results here."
            $('.no-opps').remove();

            // Let's make a new list item.
            // Let's actually clone a secret list item we've stored in the template 
            // for just this purpose.

            // NB: The html inside the LI named "#result-template" is generated
            // using the exact same template that creates the visible
            // search results.
            
            $result = $('#result-template').clone()
                .attr('id','')
                .addClass((i % 2 == 0) ? "even" : "odd")
                .appendTo('.gewgaws ul');

        }
        $result.show();
        $result.attr('id', "gewgaw-" + this.pk);

        var pairs = [
            // Each pair is of the form:
            // Class name that's used to select a DOM element, JSON field name.
            ['title', '.title'],
            ['project', '.project__name'],
            ['description', '.description'],
            ['status', 'status .value'],
            ['importance', '.importance .value'],
            ['last_touched', '.last_touched .value'],
            ['last_polled', '.last_polled .value'],
            ['canonical_bug_link', '.canonical_bug_link', 'href'],
            ['people_involved', '.people_involved .value'],
        ];

        $.fn.href = function (url) {
            this.attr('href', url);
        };

        for (var p = 0; p < pairs.length; p++) {
            var pair = pairs[p];
            var newText = this.fields[pair[0]];
            var selector = pair[1];
            var verb;
            if (typeof pair[2] == "undefined") {
                verb = "text";
            } else {
                verb = pair[2];
                //er, ok, not really a pair in this case.
                //bad variable naming ... self-flagellations.
            }
            x = $result.find(selector)[verb](newText);
        }
    };

    bugs = jsonArray[0].bugs;
    $(bugs).each( dataToDOM );

    SearchResults.bindEventHandlers();

    SearchResults.lightSearchResult(0);
};

SearchResults.lightSearchResult = function(resultIndex) {
    //console.log('lightSearchResult called');
    if($('.gewgaws li').eq(resultIndex).size() == 1) {
        $gg = $('.gewgaws li');
        //console.debug($gg);
        $gg.removeClass('lit-up')
        $gg.eq(resultIndex).addClass('lit-up').scrollIntoView();
        // FIXME: Automatically scroll when search result is expanded
        // such that its content is off-screen.
    }
};

// The PageLinks are the "prev" and "next" links that
// allow the user to browse through the list of search
// results.
SearchResults.PageLinks = {};

// Data used for manipulating these links.
SearchResults.PageLinks.manipulationData = {
    'prev': {
        '$element': $('#prev-page'), 

        'getVisibility': function() {
            // This is a function because `thisstart` changes;
            // we need to figure out during runtime whether
            // the element will be visible.
            return thisstart > 0;
        },
        
        'queryArrayCalculators': {
            // These calculate numbers we'll need to compose URLs
            // for neighboring pages.
            'start': function() {
                // The index of the *first* result to show on the linked page.
                var diff = thisend - thisstart;
                return thisstart - diff - 1;
            },
            'end': function() {
                // The index of the *last* result to show on the linked page.
                return thisstart - 1;
            }
        }
    },
    'next': {
        // See SearchResults.PageLinks.manipulationData.prev for documentation.
        '$element': $('#next-page'), 
        'getVisibility': function() {
            return thisend < (totalBugCount - 1);
        },
        'queryArrayCalculators': {
            'start': function() { return thisend + 1; },
            'end': function() {
                var diff = thisend - thisstart;
                return thisend + diff + 1;
            }
        }
    }
};

totalBugCount = 10; // FIXME: Merely temporary.

SearchResults.PageLinks.update = function() {

    for (var i in SearchResults.PageLinks.manipulationData) {
        var link = pageLinks[i];
        if (link.getVisibility()) {
            var showHide = link.getVisibility() ? 'show' : 'hide';
            link.$element[showHide]();

            /**************
             * Create URL *
             **************/
            
            // Begin with a query array
            // (shortly to be converted to query string).
            var queryArray = $('form').serializeArray(); // FIXME: 'Form' looks fishy.

            // Calculate the values of query string parameters.
            for (name in link.queryArrayCalculators) {
                var value = link.queryArrayCalculators[name]();
                queryArray.push( { 'name': name, 'value': value });
            }
            
            // Use jQuery's array to query string converter.
            var queryString = $.param(queryArray);

            // Set HREF.
            link.$element.attr('href', '/search/?' + queryString);
        }
    }
};


SearchResults.update = function(queryArray) {

    // FIXME: Temporarily disabled.
    return true;

    queryArray.push({'name': 'format', 'value': 'json'});

    queryStringFormatJSON = $.param(queryArray);

    /* Fetch JSON and put in DOM. */
    SearchResults.fetchSearchResultsToDOM(queryStringFormatJSON);

    console.debug(queryArray);

    /* Update navigation links */
    var language;
    $(queryArray).each(function () {
            if(this.name == 'language') language = this.value;
            })

    /* Update the links to neighboring pages: "prev" and "next". */
    SearchResults.PageLinks.update();

    $('#results-summary-language').text(language);
    $('#results-summary-start').text(thisstart);
    $('#results-summary-end').text(thisend);

    return false;
};

SearchResults.shortcutsEnabled = false;

SearchResults.moveSearchResultFocusDown = function () {
    SearchResults.lightSearchResult(SearchResults.getLitSearchResultIndex() + 1);
};

SearchResults.moveSearchResultFocusUp = function () {
    SearchResults.lightSearchResult(SearchResults.getLitSearchResultIndex() - 1);
};

/* vim: set ai ts=4 sts=4 et sw=4: */
