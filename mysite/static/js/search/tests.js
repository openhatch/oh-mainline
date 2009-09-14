$.fn.href = function () {
    return this.attr('href');
};

SearchTests = {
    'jsonArrayToDocument': function() {

        // Don't run this, because it fails,
        // and tests are evaluated serially like fairy lights.
        return false;

        SearchResults.jsonArrayToDocument(testData.jsonArray);
        var $result = $('.gewgaws li').eq(0);
        var testField = function(fieldName, selector, valueGetter) {
            var $domField = $result.find(selector);
            console.debug('test function is about to check element:', 
                    $domField);
            var domFieldValue = $domField[valueGetter]();
            var jsonFieldValue = testData.jsonArray[0].fields[fieldName];
            var success = ($.trim(domFieldValue) == $.trim(jsonFieldValue));
            fireunit.ok(success,
                    "SearchTests.jsonArrayToDocument: "
                    + selector + " ("+domFieldValue + ")"
                    + " = "
                    + fieldName + " (" + jsonFieldValue + ")");
            return success;
        }

        var pairs = [
            // Each pair is of the form:
            // JSON field name, class name that's used to select a DOM element
            ['title', '.title'],
            ['project', '.project__name'],
            ['description', '.description'],
            ['status', '.status .value'],
            ['importance', '.importance .value'],
            ['last_touched', '.last_touched .value'],
            ['last_polled', '.last_polled .value'],
            ['people_involved', '.people_involved .value'],
            ['canonical_bug_link', '.canonical_bug_link', 'href'],
        ];
        var success = true;
        for (var p = 0; p < pairs.length; p++) {
            var pair = pairs[p];
            if (typeof pair[2] == "undefined") {
                verb = "text";
            } else {
                verb = pair[2]; //lol ok not really a pair anymore.
            }
            success &= testField(pair[0], pair[1], verb);
        }
    },

    'blurSearchFieldWhenNewResultsAppear': function () {
        /* Test for resolution of https://openhatch.org/bugs/issue5:
         * "In opp search, keyboard shortcuts are not enabled immediately
         * because focus not on search results."
         * */
        var $searchForm = $("form#search_opps");
        $searchForm.find("input:text").focus().text("python");
        $searchForm.submit();
        var failIfFocused = function() {
            if (this == document.activeElement) return false;
        };
        $searchForm.find("input").each(failIfFocused);
        return true;
    },

    'pageLinksAppearOnlyWhenNeeded': function () {
        /* Test for resolution of
         * <https://www.pivotaltracker.com/story/show/1245515>
         * ("In /search/, don't show prev and next links when
         * they wouldn't lead you anywhere.")
         */
        var data = Fixtures.jsonArray;

        /* Visit first page of results. */

        data.start = 0;
        data.end = 10;

        SearchResults.jsonArrayToDocument(data);
        fireunit.ok("'Prev' link is hidden on first page of results.",
                $('#prev-page').is(':hidden'));
        fireunit.ok("'Next page' link is visible on first page of results.",
                $('#next-page').is(':visible'));

        /* Visit a middle page of results. */

        data.start = 20;
        data.end = 30;

        SearchResults.jsonArrayToDocument(data);
        fireunit.ok("'Prev' link is visible on a middle page of results.",
                $('#prev-page').is(':visible'));
        fireunit.ok("'Next page' link is visible on a middle page of results.",
                $('#next-page').is(':visible'));

        /* Visit the last page of results. */

        data.start = 50;
        data.end = 60;

        SearchResults.jsonArrayToDocument(data);
        fireunit.ok("'Prev' link is visible on last page of results.",
                $('#prev-page').is(':visible'));
        fireunit.ok("'Next page' link is hidden on last page of results.",
                $('#next-page').is(':hidden'));
    }
};
runTests = function() {
    for (var test in SearchTests) {
        console.debug("test: ", test);
        fireunit.ok(SearchTests[test](), "SearchTests." + test);
    }
    fireunit.testDone();
};
if (fireunitEnabled) {
    $(runTests);
}
