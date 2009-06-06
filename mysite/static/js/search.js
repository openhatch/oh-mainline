$(document).ready(function() {
	 $("#button").click(function() {
		query = ($('#query').val());
      thisPageQueryArray = $('form').serializeArray();
      thisPageQueryArrayJSON = $('form').serializeArray();
      thisPageQueryArrayJSON.format = 'json';
		Opps.fetchOppsToDOM($.param(thisPageQueryArrayJSON));


      prevPageQueryArray = $('form').serializeArray();
      prevPageQueryArray.start = thisPageQueryArray.end;
      prevPageQueryArray.end = thisPageQueryArray.end * 2 - thisPageQueryArray.start;

      nextPageQueryArray = $('form').serializeArray();
      nextPageQueryArray.start = thisPageQueryArray.start * 2 - thisPageQueryArray.end;
      nextPageQueryArray.end = thisPageQueryArray.start;
   alert('zee');
      $('#prev-page').attr('href', '/search/' + $.param(prevPageQueryArray));
      $('#next-page').attr('href', '/search/' + $.param(nextPageQueryArray));
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

/* vim:set sw=2 ts=3: */
