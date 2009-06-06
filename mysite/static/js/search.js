        function update(queryArray) {
            queryArray.push({'name': 'format', value: 'json'});

            queryStringFormatJSON = $.param(queryArray);

            /* Fetch JSON and put in DOM. */
            Opps.fetchOppsToDOM(queryStringFormatJSON);

            /* Update navigation links */
            var language, thisstart = 0, thisend = 0;
            $(queryArray).each(function () {
                if(this.name == 'language') language = this.value;
                if(this.name == 'start') thisstart = parseInt(this.value);
                if(this.name == 'end') thisend = parseInt(this.value);
                })

            console.log(thisstart, thisend);

            diff = thisend - thisstart;

            prevPageQueryArray = $('form').serializeArray();
            $(prevPageQueryArray).each(function () {
                    if (this.name == 'start') this.value = thisstart - diff - 1;
                    if (this.name == 'end') this.value = thisstart - 1;
                    });

            nextPageQueryArray = $('form').serializeArray();
            $(nextPageQueryArray).each(function () {
                    if (this.name == 'start') this.value = thisend + 1;
                    if (this.name == 'end') this.value = thisend + diff + 1;
                    });

            /* Update navigation links to reflect new query. */
            prefix = '/search/?';
            $('#prev-page').attr('href', prefix + $.param(prevPageQueryArray));
            $('#next-page').attr('href', prefix + $.param(nextPageQueryArray));

            $('#results-description-language').text(language);
            $('#results-description-start').text(thisstart);
            $('#results-description-end').text(thisend);
            
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
                var splitted_on_ampersands = this.href.split('?')[1].split('&');
                for (var index in splitted_on_ampersands) {
		    var splitted = splitted_on_ampersands[index].split('=');    
		    var key = decodeURIComponent(splitted[0]);
		    var value = decodeURIComponent(splitted[1]);
		    var fruity_pushable = {'name': key, 'value': value};
		    fruitySerialized.push(fruity_pushable);
		}
		console.log('FRUITYSERIALIZED:');
		console.log(fruitySerialized);
        console.log('SLASH FRUITYSERIALIZED:');

        return update(fruitySerialized);
        });

});

Opps = {
    'oppsQueryURL': "http://localhost:8000/search/?",
    '$oppsDOMList': $('#opps ul'),
    'fetchOppsToDOM': function (queryString) {
        url = this.oppsQueryURL + queryString + "&jsoncallback=?";
        $.getJSON(url, this.jsonArrayToDocument);
    },
    'jsonArrayToDocument': function (jsonArray) {
        $(jsonArray).each( function(i) {
                $opp = $("<li>");
                $opp.addClass(this.model);
                $opp.attr('id', "opp-" + this.pk);

                $opp.append($("<span class='project'>").text(this.fields.project));
                $opp.append($("<span class='title'>").text(this.title));
                $opp.append($("<span class='description'>").text(this.fields.description));

                // Remove only one at a time.
                // This always keeps bugs on the page, so it looks nicer, I think.
                $('#opps li').eq(i).remove();

                // Add to DOM
                $('#opps ul').append($opp);
        });
    }
}

$("#opps ul");

/* vim:set sw=4 ts=4 expandtab: */
