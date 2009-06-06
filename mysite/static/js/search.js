alert('new');

$(document).ready(function() {

        /* Takes a query and updates the page. */
        $("#button").click(function() {

            /* Get query; language for the moment. */
            query = ($('#query').val());

            /* Put form values into an associative array. */
            thisPageQueryArray = $('form').serializeArray();

            /* Make a copy of this array,
             * and tack on a request to format as JSON. */
            thisPageQueryArrayJSON = $('form').serializeArray();
            thisPageQueryArrayJSON.format = 'json';

            /* Fetch JSON and put in DOM. */
            Opps.fetchOppsToDOM($.param(thisPageQueryArrayJSON));

            /* Update navigation links to reflect new query. */
            /*
               $('#prev-page').attr('href', '/search/' + $.param(prevPageQueryArray));
               $('#next-page').attr('href', '/search/' + $.param(nextPageQueryArray));
               */

            return false;
        });
});

Opps = {
    'oppsQueryURL': "http://localhost:8000/search/?",
    '$oppsDOMList': $('#opps ul'),
    'fetchOppsToDOM': function (queryString) {
        $('#opps li').remove();
        url = this.oppsQueryURL + queryString + "&jsoncallback=?";
        $.getJSON(url, this.jsonArrayToDocument);
    },
    'jsonArrayToDocument': function (jsonArray) {
        console.log(jsonArray);
        $(jsonArray).each( function() {
                $opp = $("<li>");
                $opp.addClass(this.model);
                $opp.attr('id', "opp-" + this.pk);

                // Heading
                $h3 = $("<h3>");
                $title = $("<span>").text(this.fields.title);
                $h3.append($title);
                $opp.append($h3);

                // Summary
                $summary = $("<p>").text(this.fields.description);
                $opp.append($summary);

                console.log($opp[0]);

                // Add to DOM
                $('#opps ul').append($opp);
                console.log(Opps);

        });
    }
}

$("#opps ul");

/*
 *
 prevPageQueryArray = $('form').serializeArray();
 prevPageQueryArray.start = thisPageQueryArray.start * 2 - thisPageQueryArray.end;
 prevPageQueryArray.end = thisPageQueryArray.start;

 nextPageQueryArray = $('form').serializeArray();
 nextPageQueryArray.start = thisPageQueryArray.end;
 nextPageQueryArray.end = thisPageQueryArray.end * 2 - thisPageQueryArray.start;
 */
/* vim:set sw=4 ts=4 expandtab: */
