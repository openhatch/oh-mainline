        function update(queryArray) {
            queryArray.push({'name': 'format', value: 'json'});

            queryStringFormatJSON = $.param(queryArray);

            /* Fetch JSON and put in DOM. */
            Opps.fetchOppsToDOM(queryStringFormatJSON);

            /* Update navigation links */
            var language;
            $(queryArray).each(function () {
                if(this.name == 'language') language = this.value;
                })

            console.log(thisstart, thisend);

            diff = thisend - thisstart;

            prevPageQueryArray = $('form').serializeArray();
	    prevPageQueryArray.push( {'name': 'start', 'value': thisstart - diff - 1});
	    prevPageQueryArray.push( {'name': 'end', 'value': thisstart - 1});


            nextPageQueryArray = $('form').serializeArray();
	    nextPageQueryArray.push( {'name': 'start', 'value': thisend + 1});
	    nextPageQueryArray.push( {'name': 'end', 'value': thisend + diff + 1});

            /* Update navigation links to reflect new query. */
            prefix = '/search/?';
            $('#prev-page').attr('href', prefix + $.param(prevPageQueryArray));
            $('#next-page').attr('href', prefix + $.param(nextPageQueryArray));

            $('#results-summary-language').text(language);
            $('#results-summary-start').text(thisstart);
            $('#results-summary-end').text(thisend);
            
            console.log(thisstart);
            console.log(thisend);
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
                $opp = $("li").eq(i);
                $opp.attr('id', "opp-" + this.pk);

                $opp.find('.project').text(this.fields.project);
                $opp.find('.title').text(this.fields.title);
                $opp.find('.description').text(this.fields.description);
        });
    }
}

$("#opps ul");

/* vim:set sw=4 ts=4 expandtab: */
