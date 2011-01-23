/*
# This file is part of OpenHatch.
# Copyright (C) 2009 OpenHatch, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

$.fn.href = function () {
    return this.attr('href');
};

SearchTests = {
    'jsonArrayToDocument': function() {

        // Don't run this, because it fails,
        // and tests are evaluated serially like fairy lights.
        return false;

        SearchResults.jsonArrayToDocument(Fixtures.jsonArray);
        var $result = $('.gewgaws li').eq(0);
        var testField = function(fieldName, selector, valueGetter) {
            var $domField = $result.find(selector);
            console.debug('test function is about to check element:', 
                    $domField);
            var domFieldValue = $domField[valueGetter]();
            var jsonFieldValue = Fixtures.jsonArray[0].fields[fieldName];
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
        fireunit.ok( $('#prev-page').is(':hidden'),
                "'Prev' link is hidden on first page of results.");
        fireunit.ok( $('#next-page').is(':visible'),
                "'Next page' link is visible on first page of results.");



        /* Visit a middle page of results. */

        data.start = 1;
        data.end = 13;

        SearchResults.jsonArrayToDocument(data);
        fireunit.ok( $('#prev-page').is(':visible'),
                "'Prev' link is visible on a middle page of results.");
        fireunit.ok( $('#next-page').is(':visible'),
                "'Next page' link is visible on a middle page of results.");



        /* Visit the last page of results. */

        data.start = 1;
        data.end = 14;

        SearchResults.jsonArrayToDocument(data);
        fireunit.ok( $('#prev-page').is(':visible'),
                "'Prev' link is visible on last page of results.");
        fireunit.ok( $('#next-page').is(':hidden'),
                "'Next page' link is hidden on last page of results.");

        return true; // This value isn't important here.
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
