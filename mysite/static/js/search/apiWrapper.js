//Parent API Wrapper for Client
var APIWrapper = function(id, link) {
	this._id = Number(id);
	this.link = link;
};

APIWrapper.prototype.toString = function() {
	return this._id;
};

//Github Wrapper
var GithubWrapper = function(id, link) {
	APIWrapper.call(this, id, link);

	var linkArray = link.split("/");
	var _this = this;

	this.endpoint = 'https://api.github.com/repos/';
	this.user = linkArray[3];
	this.repo = linkArray[4];
	this.issue = linkArray[6];

	this.executeAPI = function() {
		var URL = this.endpoint+this.user+"/"+this.repo;
		$.get(URL, function(data){
			_this.populateModal(data);
		});
	};

	this.populateModal = function(data) {
		console.log(data);
		var homepage = data['homepage'];
		var description = data['description'];
		var timeSinceCreation = getAge(data['created_at']);
		var timeSinceUpdate = getAge(data['updated_at']);
		$('#projectModal').dialog('option', 'title', data['name']);
		var innerDialog = '<p><b>Description:</b> '+description+'</p>'+
						  '<p><b>Homepage:</b> '+homepage+'</p>'+
						  '<p><b>Age:</b> '+timeSinceCreation[0]+' years, '+timeSinceCreation[1]+' months, '+timeSinceCreation[2]+' days'+'</p>'+
						  '<p><b>Last Updated:</b> '+timeSinceUpdate[0]+' years, '+timeSinceUpdate[1]+' months, '+timeSinceUpdate[2]+' days'+'</p>';
		$("#projectModal").append(innerDialog);
		$("#projectModal").dialog("open");
	};
};

GithubWrapper.prototype = new APIWrapper();

//ID-Api Mapping
var mapping = {
	89: GithubWrapper
};

//Function to create APIWrapper
var createAPIWrapper = function(tracker_type, link) {
	var currentWrapper = new mapping[tracker_type](tracker_type, link);
	currentWrapper.executeAPI();
};

//Get difference between a date and right now in years, months, days
//Note: this is not exact (leap years, etc), but it's pretty good
//We could include a library like Moment.js or Date.js
var getAge = function(dateString) {
    var today = new Date();
    var startDate = new Date(dateString);
    var years = Math.floor((today - startDate) / (1000*60*60*24*365.25));
    var totalMonths = Math.floor((today - startDate)*12 / (1000*60*60*24*365.25));
    var months = totalMonths - 12*years;
    var totalDays = Math.floor((today - startDate) / (1000*60*60*24));
    var days = totalDays - 365*years - (365.25/12)*months;
    return [years, months, days];
};

$(function() {
	//Define Project Modal
	$("#projectModal").dialog({
		autoOpen: false,
		modal: true,
		open: function() {
			$("#projectModal").dialog("option", "position", {my: "center", at: "center", of: window});
			$(".ui-widget-overlay").css({
            	opacity: .3,
            	filter: "Alpha(Opacity=30)",
            	background: "black",
        	});
            $('.ui-widget-overlay').bind('click',function(){
                $('#projectModal').dialog('close');
            });
        },
        close: function(event, ui) {
        	$("#projectModal").empty();
        }
	});

	//Attach listeners to button
	$('.project_data_button').click(function() {
		var tracker_type = $(this).data("tracker");
		var	link = $(this).data("link");
		if (mapping.hasOwnProperty(tracker_type)) {
			createAPIWrapper(tracker_type, link);
		}
		else {
			console.log("Tracker_type not in mapping yet");
		}
	});

	//When window resizes, keep modal in the middle
	$(window).resize(function() {
    	$("#projectModal").dialog("option", "position", {my: "center", at: "center", of: window});
	});
});
