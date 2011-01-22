/*
# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2010 OpenHatch
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

function MapTests(){

    var $mappablePeople = [];
    for (var person_id in mapController.get_person_id2data()) {
        $mappablePeople.push($('#person_summary_'+person_id));
    }

    tester.ok($mappablePeople.length >= 3, "There are at least three visible LIs inside #people-list.");

    //first we highlight person 3
    var $dontClickMyMarker = $mappablePeople[2];
    $dontClickMyMarker.addClass("highlighted");

    //make sure there are at least three people
    tester.compare($dontClickMyMarker.size(), 1, "there are at least three people");

    /*
     * Test that clicking on a marker highlights the correlated list item.
     */
    var $clickMyMarker = $mappablePeople[0];

    tester.compare($clickMyMarker.size(), 1, "there is at least one person");

    //make sure we're not highlighted to being with
    tester.ok(!$clickMyMarker.hasClass("highlighted"), "Person is not highlighted initially");

    // Assume that markers' click handlers are set to highlightPerson(id)
    
    // Emulate the click of a marker.
    var personID = $clickMyMarker.get(0).id.split("_")[2];
    mapController.highlightPerson(personID);

    tester.ok($clickMyMarker.hasClass("highlighted"), "Highlight person after marker onclick function was fired");

    //make sure we unhighlight the person who we highlighted at the beginning
    tester.ok(!$dontClickMyMarker.hasClass("highlighted"), "Person who was highlighted gets unhighlighted when we click someone else on the map.");

    /*
     * Test that clicking on a list item highlights the person.
     */
    var $clickMe = $mappablePeople[1];
    
    tester.compare($clickMe.size(), 1, "there are at least two people in the list");

    tester.ok(!$clickMe.hasClass("highlighted"), "person is not highlighted initially");

    // Click a person
    $clickMe.click();

    tester.ok($clickMe.hasClass("highlighted"), "A clicked person becomes highlighted");

    tester.ok(!$clickMyMarker.hasClass("highlighted"), "previously highlighted person is not highlighted after we click someone else");

    // Test that person_location object has all the right person_ids
    var mappableID2data = mapController.get_person_id2data();
    for (var person_id in mappableID2data) {
        tester.compare(typeof mapController.person_locations[""+person_id], "undefined",
                "The mapping of Django-side Person IDs to " +
                "Google Map-style location objects contains the ID " +
                person_id);
    }

    tester.testDone();

}

$(MapTests);
