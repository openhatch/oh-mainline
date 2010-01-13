function MapTests(){

    /*
     * Test that clicking on a marker highlights the correlated list item.
     */
    var $clickMyMarker = $('#people-list li:0');

    tester.compare($clickMyMarker.size(), 1);

    //make sure we're not highlighted to being with
    tester.ok(!$highlightMe.hasClass("highlighted"), "Person is not highlighted initially");

    // Assume that markers' click handlers are set to highlightPerson(id)
    
    // Emulate the click of a marker.
    var personID = $clickMyMarker.get(0).id.split("_")[2]
    highlightPerson(personID);

    tester.ok($clickMyMarker.hasClass("highlighted"), "Highlight person after marker onclick function was fired");

    /*
     * Test that clicking on a list item highlights the person.
     */
    var $clickMe = $('#people-list li:1');
    
    tester.compare($clickMe.size(), 1);

    tester.ok(!$clickMe.hasClass("highlighted"), "person is not highlighted initially");

    // Click a person
    $clickMe.click();

    tester.ok($clickMe.hasClass("highlighted"), "A clicked person becomes highlighted");
}

$(MapTests);
