function MapTests(){
    //first we highlight person 3
    var $dontClickMyMarker = $('#people-list li:eq(2)');
    $dontClickMyMarker.addClass("highlighted");

    //make sure there are at least three people
    tester.compare($dontClickMyMarker.size(), 1, "there are at least three people");

    /*
     * Test that clicking on a marker highlights the correlated list item.
     */
    var $clickMyMarker = $('#people-list li:eq(0)');

    tester.compare($clickMyMarker.size(), 1, "there is at least one person");

    //make sure we're not highlighted to being with
    tester.ok(!$clickMyMarker.hasClass("highlighted"), "Person is not highlighted initially");

    // Assume that markers' click handlers are set to highlightPerson(id)
    
    // Emulate the click of a marker.
    var personID = $clickMyMarker.get(0).id.split("_")[2];
    map.highlightPerson(personID);

    tester.ok($clickMyMarker.hasClass("highlighted"), "Highlight person after marker onclick function was fired");

    //make sure we unhighlight the person who we highlighted at the beginning
    tester.ok(!$dontClickMyMarker.hasClass("highlighted"), "Person who was highlighted gets unhighlighted when we click someone else on the map.");

    /*
     * Test that clicking on a list item highlights the person.
     */
    var $clickMe = $('#people-list li:eq(1)');
    
    tester.compare($clickMe.size(), 1, "there are at least two people in the list");

    tester.ok(!$clickMe.hasClass("highlighted"), "person is not highlighted initially");

    // Click a person
    $clickMe.click();

    tester.ok($clickMe.hasClass("highlighted"), "A clicked person becomes highlighted");

    tester.ok(!$clickMyMarker.hasClass("highlighted"), "previously highlighted person is not highlighted after we click someone else");

    tester.testDone();


}

$(MapTests);
