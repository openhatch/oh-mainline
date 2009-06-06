$(document).ready(function() {

        function update(queryArray) {

            queryArray.push({'name': 'format', value: 'json'});

            queryStringFormatJSON = $.param(queryArray);

            /* Fetch JSON and put in DOM. */
            Opps.fetchOppsToDOM(queryStringFormatJSON);

            /* Update navigation links */
            var oldstart = 0, oldend = 0;
            $(queryArray).each(function () {
                if(this.name == 'start') oldstart = parseInt(this.value);
                if(this.name == 'end') oldend = parseInt(this.value);
                })

            console.log(oldstart, oldend);

            diff = oldend - oldstart;

            prevPageQueryArray = $('form').serializeArray();
            $(prevPageQueryArray).each(function () {
                    if (this.name == 'start') this.value = oldstart - diff;
                    if (this.name == 'end') this.value = oldstart;
                    }
                    );

            prevPageQueryArray = $('form').serializeArray();
            $(prevPageQueryArray).each(function () {
                    if (this.name == 'start') this.value = oldend;
                    if (this.name == 'end') this.value = oldend + diff;
                    });

            /* Update navigation links to reflect new query. */
            $('#prev-page').attr('href', '/search/' + $.param(prevPageQueryArray));
            $('#next-page').attr('href', '/search/' + $.param(nextPageQueryArray));

            return false;
        };

        /* Takes a query and updates the page. */
        $("#button").click(function() {
            /* Get query; language for the moment. */
            query = ($('#query').val());

            /* Put form values into an associative array. */
            update($('form').serializeArray());
            });


        $('#prev-page, #next-page').click(function() {
                
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

/* vim:set sw=4 ts=4 expandtab: */
