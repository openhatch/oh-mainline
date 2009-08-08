SearchTests = {
    'jsonArrayToDocument': function() {
        Search.jsonArrayToDocument(testData.jsonArray);
        var testField = function(className, fieldName) {
            var domText = $('.gewgaws li').eq(0).find('.'+className).text();
            var jsonText = testData.jsonArray[0].fields[fieldName];
            var success = (domText == jsonText);
            fireunit.ok(success, "SearchTests.jsonArrayToDocument: " + className);
            return success;
        }
        var pairs = {
            ['title', 'title'],
            ['project__name', 'project__name'],
        };
        var success = true;
        for (var pair in pairs) {
            success &= testField(pair[0], pair[1]);
        }
    }
};
runTests = function() {
    for (var test in SearchTests) {
        console.debug(test);
        fireunit.ok(testSearch[test](), "SearchTests." + test);
    }
    fireunit.testDone();
};
if (fireunitEnabled) {
    $(runTests);
}
