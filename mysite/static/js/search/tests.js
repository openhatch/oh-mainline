testGewgaws = {};
testGewgaws.jsonArrayToDocument = function() {
    Gewgaws.jsonArrayToDocument(testData.jsonArray);
    return $('.gewgaws li').eq(0).find('.title').text() == testData.jsonArray[0].fields.title;
};
runTests = function() {
    for (test in testGewgaws) {
        console.debug(test);
        fireunit.ok(testGewgaws[test](), "testGewgaws." + test);
    }
    fireunit.testDone();
};
if (fireunitEnabled) {
    $(runTests);
}
