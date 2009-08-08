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

        SearchResults.lightSearchResult(0);

        $('#expand-all-link').click(function() {
            $('.gewgaws li').addClass('expanded');
            return false;
            });

        $('#collapse-all-link').click(function() {
            $('.gewgaws li').removeClass('expanded');
            return false;
            });

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

        /* Takes a query and updates the page. */
        $("#button").click(function() {
                /* Put form values into an associative array. */
                return SearchResults.update($('form').serializeArray());
                });


        $('#prev-page, #next-page').click(function() {
                /* Take the HREF and convert to wacky serializeArray, send to update() */
                var fruitySerialized = new Array();
                var splitted_on_ampersands = this.href.split('?')[1].split('&');
                for (var index in splitted_on_ampersands) {
                var splitted = splitted_on_ampersands[index].split('=');    
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
                /*
                console.log('FRUITYSERIALIZED:');
                console.log(fruitySerialized);
                console.log('SLASH FRUITYSERIALIZED:');
                */

                return SearchResults.update(fruitySerialized);
        });

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
                $gewgaw = $(this.parentNode.parentNode);
                $gewgaw.toggleExpanded();
                return false;
                });

        $('.show-details').click(function () {
                $gewgaw = $(this.parentNode.parentNode.parentNode);
                $gewgaw.toggleExpanded();
                return false;
                });

        $('.first-line a.title').click(function () {
                $gewgaw = $(this.parentNode.parentNode.parentNode);
                $gewgaw.toggleExpanded();
                return false;
                });
}

SearchResults.focusSearchInput = function () {
    //console.log('focus search input called');
    $("#opps form input[type='text']").focus();
};

SearchResults.queryURL = "/search/?";

SearchResults.$gewgawsDOMList = $('.gewgaws ul');

SearchResults.getLitGewgawIndex = function() {
    // FIXME: Remember the index of the lit gewgaw in Javascript,
    // and avoid going through CSS.
    return $('.gewgaws li').index($('.lit-up')[0]);
};

SearchResults.fetchSearchResultsToDOM = function (queryString) {
    url = this.queryURL + queryString + "&jsoncallback=?";
    $.getJSON(url, this.jsonArrayToDocument);
    SearchResults.lightSearchResult(0);
};

SearchResults.jsonArrayToDocument = function (jsonArray) {
    $('.gewgaws li').hide();

    // Create a results list if there's isn't one already.
    var noResultsList = $('#opps ul').size() == 0;
    if (noResultsList) { $("<ul>").appendTo('#opps'); }

    SearchResults.setSearchControlsForTheHeartOfTheSunAlsoMakeThemVisible();

    var dataToDOM = function(i) {
        // Add data from JSON array element to DOM.
        $gewgaw = $(".gewgaws li").eq(i);

        // This function updates the result list.
        // It will attempt to recycle list items
        // that are already in the DOM.
        // However...
        if ( $gewgaw.size() == 0 ) {

            console.log('creating a list item');

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
            
            $gewgaw = $('#result-template').clone()
                .attr('id','')
                .addClass((i % 2 == 0) ? "even" : "odd")
                .appendTo('.gewgaws ul');

            console.debug($gewgaw);
        }
        $gewgaw.show();
        $gewgaw.attr('id', "gewgaw-" + this.pk);

        $gewgaw.find('.project').text(this.fields.project);
        $gewgaw.find('.title').text(this.fields.title);
        $gewgaw.find('.description').text(this.fields.description);
    };

    $(jsonArray).each( dataToDOM );

    SearchResults.bindEventHandlers();

    SearchResults.lightSearchResult(0);
};

SearchResults.lightSearchResult = function(gewgawIndex) {
    //console.log('lightSearchResult called');
    if($('.gewgaws li').eq(gewgawIndex).size() == 1) {
        $gg = $('.gewgaws li');
        //console.debug($gg);
        $gg.removeClass('lit-up')
        $gg.eq(gewgawIndex).addClass('lit-up').scrollIntoView();
        // FIXME: Automatically scroll when gewgaw is expanded such that its content is off-screen.
    }
    else {
        console.log('no gewgaw to highlight');
    }
};

SearchResults.update = function(queryArray) {
    queryArray.push({'name': 'format', value: 'json'});

    queryStringFormatJSON = $.param(queryArray);

    /* Fetch JSON and put in DOM. */
    SearchResults.fetchSearchResultsToDOM(queryStringFormatJSON);

    /* Update navigation links */
    var language;
    $(queryArray).each(function () {
            if(this.name == 'language') language = this.value;
            })

    diff = thisend - thisstart;

    prevPageQueryArray = $('form').serializeArray();
    prevPageQueryArray.push( {'name': 'start', 'value': thisstart - diff - 1});
    prevPageQueryArray.push( {'name': 'end', 'value': thisstart - 1});

    nextPageQueryArray = $('form').serializeArray();
    nextPageQueryArray.push( {'name': 'start', 'value': thisend + 1});
    nextPageQueryArray.push( {'name': 'end', 'value': thisend + diff + 1});

    /* Update navigation links to reflect new query. */
    prefix = '/search/?';
    $('#prev-page').attr('href', prefix + $.param(prevPageQueryArray));
    $('#next-page').attr('href', prefix + $.param(nextPageQueryArray));

    $('#results-summary-language').text(language);
    $('#results-summary-start').text(thisstart);
    $('#results-summary-end').text(thisend);

    return false;
};

SearchResults.moveSearchResultFocusDown = function () {
    SearchResults.lightSearchResult(SearchResults.getLitGewgawIndex() + 1);
};

SearchResults.moveSearchResultFocusUp = function () {
    SearchResults.lightSearchResult(SearchResults.getLitGewgawIndex() - 1);
};

SearchResults.setSearchControlsForTheHeartOfTheSunAlsoMakeThemVisible = function () {
    $('.search-result-control').show();
};

/* vim: set ai ts=4 sts=4 et sw=4: */
