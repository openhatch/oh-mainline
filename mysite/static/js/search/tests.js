SearchTests = {
    'jsonArrayToDocument': function() {
        SearchResults.jsonArrayToDocument(testData.jsonArray);
        var testField = function(className, fieldName) {
            var domText = $('.gewgaws li').eq(0).find('.'+className).text();
            var jsonText = testData.jsonArray[0].fields[fieldName];
            var success = (domText == jsonText);
            fireunit.ok(success, "SearchTests.jsonArrayToDocument: "
                    + className + " <-- " + fieldName);
            return success;
        }
        // Class name that selects a DOM element, JSON field name.
        var pairs = [
            ['title', 'title'],
            ['project__name', 'project__name'],
            ['description', 'description'],
            ['status', 'status'],
            ['importance', 'importance'],
            ['last_touched', 'last_touched'],
            ['last_polled', 'last_polled'],
            ['canonical_bug_link', 'canonical_bug_link'],
            ['people_involved_count', 'people_involved_count'],
        ];
        var success = true;
        for (var p = 0; p < pairs.length; p++) {
            var pair = pairs[p];
            success &= testField(pair[0], pair[1]);
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
