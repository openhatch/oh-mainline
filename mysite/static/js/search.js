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

            nextPageQueryArray = $('form').serializeArray();
            $(nextPageQueryArray).each(function () {
                    if (this.name == 'start') this.value = oldend;
                    if (this.name == 'end') this.value = oldend + diff;
                    });

            /* Update navigation links to reflect new query. */
            $('#prev-page').attr('href', '/search/' + $.param(prevPageQueryArray));
            $('#next-page').attr('href', '/search/' + $.param(nextPageQueryArray));

            return false;
        };

$(document).ready(function() {

        /* Takes a query and updates the page. */
        $("#button").click(function() {
            /* Put form values into an associative array. */
            return update($('form').serializeArray());
            });


        $('#prev-page, #next-page').click(function() {
                /* Take the HREF and convert to wacky serializeArray, send to update() */
		var fruitySerialized = new Array();
                var splitted_on_ampersands = this.href.split('&');
                for (var keyvalue in splitted_on_ampersands) {
		    var splitted = keyvalue.split('=');    
		    var key = splitted[0];
		    var value = splitted[1];
		    var fruity_pushable = {'name': key, 'value': value};
		    fruitySerialized.push(fruity_pushable);
		}
                return update(fruitySerialized);
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

                // Add to DOM
                $('#opps ul').append($opp);
        });
    }
}

$("#opps ul");

/* vim:set sw=4 ts=4 expandtab: */
