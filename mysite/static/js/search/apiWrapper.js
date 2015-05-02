//Parent API Wrapper for Client
var APIWrapper = function(type, id, link) {
	this._type = type;
	this._id = id;
	this._link = link;
	console.log(this);
};

APIWrapper.prototype.toString = function() {
	return this._type;
};

//Github Wrapper
var GithubWrapper = function(type, id, link) {
	APIWrapper.call(this, type, id, link);
	var _this = this;
	this.endpoint = 'https://api.github.com/repos/';

	var linkArray = this._link.split("/");
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

//Google Code Wrapper
var GoogleWrapper = function(type, id, link) {

};

GoogleWrapper.prototype = new APIWrapper();

//Bugzilla.Mozilla Wrapper
var BugzillaMozilla = function(type, id, link) {
	APIWrapper.call(this, type, id, link);
	var _this = this;
	this.bugEndpoint = 'https://bugzilla.mozilla.org/rest/bug/';
	this.productEndpoint = 'https://bugzilla.mozilla.org/rest/product/'; 

	var linkArray = this._link.split("=");
	this.bugID = linkArray[1];

	this.executeAPI = function() {
		var URL = this.bugEndpoint+this.bugID;
		$.get(URL, function(data) {
			_this.executeProductAPI(data["bugs"][0]["product"], data["bugs"][0]["component"]);
		});
	};

	this.executeProductAPI = function(product, componentName) {
		var URL = this.productEndpoint+product;
		$.get(URL, function(data) {
			data['products'][0]['components'].forEach(function (component) {
				if (component['name'] == componentName) {
					_this.populateModal(data['products'][0], component);
					console.log("Found our component");
				}
			});
		});
	};

	this.populateModal = function(product, component) {
		var productName = product['name'];
		var productDescription = product['description']
		var componentName = component['name'];
		var componentDescription = component['description'];
		$('#projectModal').dialog('option', 'title', productName+":"+componentName);
		var innerDialog = '<p><b>Product:</b> '+productName+'</p>'+
						  '<p><b>Product Desciption:</b> '+productDescription+'</p>'+
						  '<p><b>Component:</b> '+componentName+'</p>'+
						  '<p><b>Component Description:</b>'+componentDescription+'</p>';
		$('#projectModal').append(innerDialog);
		$('#projectModal').dialog("open");
	};
};

BugzillaMozilla.prototype = new APIWrapper();

//ID-Api Mapping
var mapping = {
	89: GithubWrapper,
	//Bugzilla Trackers
	66: {
		103: BugzillaMozilla
		//92: Gnome
	}
	//TODO Google Code, ScourgeForce
};

//Function to create APIWrapper
var createAPIWrapper = function(tracker_type, tracker_id, link) {
	if (typeof mapping[tracker_type] == 'object') {
		var currentWrapper = new mapping[tracker_type][tracker_id](tracker_type, tracker_id, link);
	} else {
		var currentWrapper = new mapping[tracker_type](tracker_type, tracker_id, link);
	}
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

//Generate Empty Modal
var populateEmptyModal = function() {
	$('#projectModal').dialog('option', 'title', 'No Project Data');
	var innerDialog = "<p>Sorry! This project's API has not been added yet!</p>";
	$('#projectModal').append(innerDialog);
	$('#projectModal').dialog('open');
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
		var tracker_id = $(this).data("id");
		var	link = $(this).data("link");
		if (mapping.hasOwnProperty(tracker_type)) {
			createAPIWrapper(tracker_type, tracker_id, link);
		}
		else {
			console.log(tracker_type);
			console.log("Tracker_type not in mapping yet");
			populateEmptyModal();
		}
	});

	//When window resizes, keep modal in the middle
	$(window).resize(function() {
    	$("#projectModal").dialog("option", "position", {my: "center", at: "center", of: window});
	});
});
