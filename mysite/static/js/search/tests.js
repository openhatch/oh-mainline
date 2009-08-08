$.fn.href = function () {
    return this.attr('href');
};

SearchTests = {
    'jsonArrayToDocument': function() {
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
    }
};
runTests = function() {
    for (var test in SearchTests) {
        console.debug(test);
        fireunit.ok(SearchTests[test](), "SearchTests." + test); }
    fireunit.testDone();
};
if (fireunitEnabled) {
    $(runTests);
}
