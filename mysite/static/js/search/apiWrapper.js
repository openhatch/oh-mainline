/**
apiWrapper.js

The Objects in this file represent wrapper around various bug tracker APIs.
When possible, these wrappers inherit from a parent. They all inherit
from APIWrapper. Individual wrappers like JiraMifos will inherit
from the more general Mifos wrapper. This allows additional wrappers
to be added for individual cases easily. You can override any attribute
or method in a child by simply writing the method yourself in that class.

All Wrapper objects must contain - or inherit - an executeAPI() function
as well as a populateModal() function. The first of these two is the first
and perhaps last set of function that makes the API request (callback should
always be used in asynchronous situations). populateModal() simply
fills in the popup modal with data recieved by the API request.

Important distinctions made in this file - tracker_type, tracker_id.
The tracker_type is one level of generalization over tracker_id. For
example, tracker_type can be an integer that refers to the Launchpad
bug tracker. However, each instance of Launchpad (heat, horizon, etc)
will recieve their own tracker _id. 

IMPORTANT: Make sure you have CORS enabled if you are developing locally.
*/

/**
	TODO: 
		1) Finish Python BugTracker
		2) Make timeout on spinny wheel thing
			Does that mean timeout on request too?
			Fill the modal with a different message
*/


/**
DataCache is a local (not currently using cookies) record of which APIs
have been queried. This allows queries that take a long time to be
remembered and loaded quickly. It also helps alleviate API use in cases
where the API has some sort of limit (Github, for instance).
*/
var DataCache = {};

//Add some data to the cache
var addToCache = function(data) {
	DataCache[data.tracker_id] = data.tracker_data;
};

//Check is data is in the cache
var isInDataCache = function(_id) {
	if (DataCache.hasOwnProperty(_id)) {
		return true;
	} else {
		return false;
	}
}

//API Wrappers
//Parent API Wrapper for Client
var APIWrapper = function(type, id, link) {
	this._type = type;
	this._id = id;
	this._link = link;
};
APIWrapper.prototype.toString = function() {
	return this._type;
};

//Github Wrapper
var GithubWrapper = function(type, id, link) {
	APIWrapper.call(this, type, id, link);
	this.endpoint = 'https://api.github.com/repos/';
	this.user = this._link.split("/")[3];
	this.repo = this._link.split("/")[4];
	this.issue = this._link.split("/")[6];
	var _this = this;

	this.executeAPI = function() {
		$("#projectModal").dialog("open");
		var URL = this.endpoint+this.user+"/"+this.repo;
		$.ajax({
			url: URL,
			timeout: 3000,
			success: function(data) {
				addToCache({
					tracker_id: _this._id, 
					tracker_data: [data]
				});
				_this.populateModal(data);
			},
			error: function(jqXHR, textStatus, errorThrown) {
				if (textStatus == 'timeout') {
					populateTimeoutModal();
				} else {
					console.log(jqXHR, textStatus, errorThrown);
					populateErrorModal(textStatus);
				}
			}
		});
	};

	this.populateModal = function(data) {
		var homepage = data['homepage'];
		var description = data['description'];
		if (description.length > 200) {
			var sentences = description.split(". ");
			description = sentences[0]+'. '+sentences[1]+'. '+sentences[2]+'.';
		}
		var timeSinceCreation = getAge(data['created_at']);
		var timeSinceUpdate = getAge(data['updated_at']);
		$('#projectModal').dialog('option', 'title', data['name']);
		var innerDialog = '<p><b>Description:</b> '+description+'</p>'+
						  '<p><b>Homepage:</b> <a href='+homepage+' >'+
						  	homepage+'</a></p>'+
						  '<p><b>Project Age:</b> '+timeSinceCreation[0]+
						  	' years, '+timeSinceCreation[1]+' months, '+
						  	timeSinceCreation[2]+' days'+'</p>'+
						  '<p><b>Last Updated:</b> '+timeSinceUpdate[0]
						  	+' years, '+timeSinceUpdate[1]+' months, '
						  	+timeSinceUpdate[2]+' days'+'</p>';
		stopLoad();
		$("#projectModal").append(innerDialog);
	};
};
GithubWrapper.prototype = Object.create(APIWrapper.prototype);

//Bugzilla.Mozilla Wrapper
var BugzillaMozilla = function(type, id, link) {
	APIWrapper.call(this, type, id, link);
	this.bugEndpoint = 'https://bugzilla.mozilla.org/rest/bug/';
	this.productEndpoint = 'https://bugzilla.mozilla.org/rest/product/'; 
	this.bugID = this._link.split("=")[1];
	var _this = this;

	this.executeAPI = function() {
		$('#projectModal').dialog("open");
		var URL = this.bugEndpoint+this.bugID;
		$.ajax({
			url: URL,
			timeout: 3000,
			success: function(data) {
				_this.executeProductAPI(
					data["bugs"][0]["product"], data["bugs"][0]["component"]
				);
			},
			error: function(jqXHR, textStatus, errorThrown) {
				if (textStatus == 'timeout') {
					populateTimeoutModal();
				} else {
					console.log(jqXHR, textStatus, errorThrown);
					populateErrorModal(textStatus);
				}
			}
		});
	};

	this.executeProductAPI = function(product, componentName) {
		var URL = this.productEndpoint+product;
		$.ajax({
			url: URL,
			timeout: 3000,
			success: function(data) {
				data['products'][0]['components'].forEach(function (component) {
					if (component['name'] == componentName) {
						addToCache({
							tracker_id: _this._id, 
							tracker_data: [data['products'][0], component]
						});
						_this.populateModal(data['products'][0], component);
					}
				});
			},
			error: function(jqXHR, textStatus, errorThrown) {
				if (textStatus == 'timeout') {
					populateTimeoutModal();
				} else {
					console.log(jqXHR, textStatus, errorThrown);
					populateErrorModal(textStatus);
				}
			}
		});
	};

	this.populateModal = function(product, component) {
		var productName = product['name'];
		var productDescription = product['description'];
		if (productDescription.length > 200) {
			var sentences = productDescription.split(". ");
			productDescription = sentences[0]+'. '+sentences[1]+'. '+sentences[2]+'.';
		}
		var componentName = component['name'];
		var componentDescription = component['description'];
		$('#projectModal').dialog('option', 'title', productName+":"+componentName);
		var innerDialog = '<p><b>Product:</b> '+productName+'</p>'+
						  '<p><b>Product Desciption:</b> '+productDescription+'</p>'+
						  '<p><b>Component:</b> '+componentName+'</p>'+
						  '<p><b>Component Description:</b>'
						  	+componentDescription+'</p>';
		stopLoad();
		$('#projectModal').append(innerDialog);
	};
};
BugzillaMozilla.prototype = Object.create(APIWrapper.prototype);

//Jira Wrapper - Main Wrapper for Jira Bug Tracker
var JiraWrapper = function(type, id, link) {
	APIWrapper.call(this, type, id, link);
	this.issue = this._link.split("/")[4];
	var _this = this;

	this.executeAPI = function() {
		$('#projectModal').dialog("open");
		var URL = this.endpoint+this.issue;
		$.ajax({
			url: URL,
			timeout: 3000,
			success: function(data) {
				_this.executeProjectAPI(data, data['fields']['project']['self']);
			},
			error: function(jqXHR, textStatus, errorThrown) {
				if (textStatus == 'timeout') {
					populateTimeoutModal();
				} else {
					console.log(jqXHR, textStatus, errorThrown);
					populateErrorModal(textStatus);
				}
			}
		});
	};

	this.executeProjectAPI = function(issueData, URL) {
		$.ajax({
			url: URL,
			timeout: 3000,
			success: function(data) {
				addToCache({
					tracker_id: _this._id, 
					tracker_data: [issueData, data]
				});
				_this.populateModal(issueData, data);
			},
			error: function(jqXHR, textStatus, errorThrown) {
				if (textStatus == 'timeout') {
					populateTimeoutModal();
				} else {
					console.log(jqXHR, textStatus, errorThrown);
					populateErrorModal(textStatus);
				}
			}
		});
	};

	this.populateModal = function(issueData, projectData) {
		var projectName = projectData['name'];
		$('#projectModal').dialog('option', 'title', projectName);
		var startDate = projectData['versions'][0]['releaseDate'];
		var timeSinceCreation = getAge(startDate);
		var innerDialog = '<p><b>Project Age:</b> '+timeSinceCreation[0]+
							' years, '+timeSinceCreation[1]+' months, '+
							timeSinceCreation[2]+' days'+'</p>';
		stopLoad();
		$('#projectModal').append(innerDialog);
	};
};
JiraWrapper.prototype = Object.create(APIWrapper.prototype);


//Jira Mifos Wrapper
//Requires: this.endpoint - defines API endpoint
//Optional: this.populateModal - overrides the method in the Parent
var JiraMifos = function(type, id, link) {
	this.endpoint = 'https://mifosforge.jira.com/rest/api/latest/issue/';
	JiraWrapper.call(this, type, id, link);
};
JiraMifos.prototype = Object.create(JiraWrapper.prototype);

//Jira Cyanogenmod Wrapper
//Requires: this.endpoint - defines API endpoint
//Optional: this.populateModal - overrides the method in the Parent
var JiraCyanogenmod = function(type, id, link) {
	this.endpoint = 'https://jira.cyanogenmod.org/rest/api/latest/issue/';
	JiraWrapper.call(this, type, id, link);

	this.populateModal = function(issueData, projectData) {
		var projectName = projectData['name'];
		$('#projectModal').dialog('option', 'title', projectName);
		var projectDescription = projectData['description'];
		if (projectDescription.length > 200) {
			var sentences = projectDescription.split(". ");
			projectDescription = sentences[0]+'. '+sentences[1]+'. '+sentences[2]+'.';
		}
		var startDate = projectData['versions'][0]['releaseDate'];
		var timeSinceCreation = getAge(startDate);
		var innerDialog = '<p><b>Description:</b> '+projectDescription+'</p>'+
		                  '<p><b>Project Age:</b> '+timeSinceCreation[0]+
		                  	' years, '+timeSinceCreation[1]+' months, '+
		                  	timeSinceCreation[2]+' days'+'</p>';
		stopLoad();
		$('#projectModal').append(innerDialog);
	};
};
JiraCyanogenmod.prototype = Object.create(JiraWrapper.prototype);

//Sympy Wrapper - an example of simply going to the souce code for data
var SympyWrapper = function(type, id, link) {
	var sourceCode = "https://github.com/sympy/sympy/issues/foobar";
	GithubWrapper.call(this, type, id, sourceCode);
};
SympyWrapper.prototype = Object.create(GithubWrapper.prototype);

//Launchpad wrapper - Main Wrapper for bugs.launchpad.net
var LaunchpadWrapper = function(type, id, link) {
	APIWrapper.call(this, type, id, link);
	this.endpoint = 'https://api.launchpad.net/devel/';
	this.project = this._link.split("/")[3];
	var _this = this;

	this.executeAPI = function() {
		$('#projectModal').dialog("open");
		var URL = this.endpoint + this.project;
		$.ajax({
			url: URL,
			timeout: 3000,
			success: function(data) {
				addToCache({
					tracker_id: _this._id, 
					tracker_data: [data]
				});
				_this.populateModal(data);
			},
			error: function(jqXHR, textStatus, errorThrown) {
				if (textStatus == 'timeout') {
					populateTimeoutModal();
				} else {
					console.log(jqXHR, textStatus, errorThrown);
					populateErrorModal(textStatus);
				}
			}
		});
	};

	this.populateModal = function(data) {
		var projectName = data['name'];
		$('#projectModal').dialog('option', 'title', projectName);
		var description = data['description'];
		if (description.length > 200) {
			var sentences = description.split(". ");
			description = sentences[0]+'. '+sentences[1]+'. '+sentences[2]+'.';
		}
		var homepage = data['homepage_url'];
		var date_created = data['date_created'];
		var timeSinceCreation = getAge(date_created);
		var innerDialog = '<p><b>Description:</b> '+description+'</p>'+
						  '<p><b>Homepage:</b> <a href='+homepage+' >'+
						  	homepage+'</a></p>'+
						  '<p><b>Project Age:</b> '+timeSinceCreation[0]+
						  	' years, '+timeSinceCreation[1]+' months, '+
						  	timeSinceCreation[2]+' days'+'</p>';
		stopLoad();
		$('#projectModal').append(innerDialog);
	};
};
LaunchpadWrapper.prototype = Object.create(APIWrapper.prototype);

//Horizon Launchpad Wrapper
var HorizonLaunchpad = function(type, id, link) {
	LaunchpadWrapper.call(this, type, id, link);
};
HorizonLaunchpad.prototype = Object.create(LaunchpadWrapper.prototype);

//Heat LaunchPad Wrapper
var HeatLaunchpad = function(type, id, link) {
	LaunchpadWrapper.call(this, type, id, link);
};
HeatLaunchpad.prototype = Object.create(LaunchpadWrapper.prototype);

//UbuntuQualityManualTestcases LaunchPad Wrapper
var UbuntuQualityManualTestcasesLaunchpad = function(type, id, link) {
	LaunchpadWrapper.call(this, type, id, link);

	this.populateModal = function(data) {
		var projectName = data['name'];
		$('#projectModal').dialog('option', 'title', projectName);
		var description = data['description'];
		if (description.length > 200) {
			var sentences = description.split(". ");
			description = sentences[0]+'. '+sentences[1]+'. '+sentences[2]+'.';
		}
		var date_created = data['date_created'];
		var timeSinceCreation = getAge(date_created);
		var innerDialog = '<p><b>Description:</b> '+description+'</p>'+
						  '<p><b>Project Age:</b> '+timeSinceCreation[0]+
						  	' years, '+timeSinceCreation[1]+' months, '+
						  	timeSinceCreation[2]+' days'+'</p>';
		stopLoad();
		$('#projectModal').append(innerDialog);
	};
};
UbuntuQualityManualTestcasesLaunchpad.prototype = 
	Object.create(LaunchpadWrapper.prototype);

//UbuntuQualityAutopilotTestcases LaunchPad Wrapper
var UbuntuQualityAutopilotTestcasesLaunchpad = function(type, id, link) {
	LaunchpadWrapper.call(this, type, id, link);

	this.populateModal = function(data) {
		var projectName = data['name'];
		$('#projectModal').dialog('option', 'title', projectName);
		var description = data['description'];
		if (description.length > 200) {
			var sentences = description.split(". ");
			description = sentences[0]+'. '+sentences[1]+'. '+sentences[2]+'.';
		}
		var date_created = data['date_created'];
		var timeSinceCreation = getAge(date_created);
		var innerDialog = '<p><b>Description:</b> '+description+'</p>'+
						  '<p><b>Project Age:</b> '+timeSinceCreation[0]+
						  	' years, '+timeSinceCreation[1]+' months, '+
						  	timeSinceCreation[2]+' days'+'</p>';
		stopLoad();
		$('#projectModal').append(innerDialog);
	};
};
UbuntuQualityAutopilotTestcasesLaunchpad.prototype = 
	Object.create(LaunchpadWrapper.prototype);

//Stratagus LaunchPad Wrapper
var StratagusLaunchpad = function(type, id, link) {
	LaunchpadWrapper.call(this, type, id, link);
};
StratagusLaunchpad.prototype = Object.create(LaunchpadWrapper.prototype);

//Openhatch Wrapper
var OpenhatchWrapper = function(type, id, link) {
	GithubWrapper.call(this, type, id, link);
};
OpenhatchWrapper.prototype = Object.create(GithubWrapper.prototype);

//Python Wrapper - an example of scraping the 
//web pages of the tracker for information
var PythonWrapper = function(type, id, link) {
	APIWrapper.call(this, type, id, link);
	this.endpoint = 'http://bugs.python.org';
	var _this = this;

	this.executeAPI = function() {
		$('#projectModal').dialog("open");
		$.ajax({
			url: _this.endpoint,
			type: 'GET',
			dataType: 'html',
			timeout: 3000,
			success: function(html) {
				_this.populateModal(html);
			},
			error: function(jqXHR, textStatus, errorThrown) {
				if (textStatus == 'timeout') {
					populateTimeoutModal();
				} else {
					console.log(jqXHR, textStatus, errorThrown);
					populateErrorModal(textStatus);
				}
			}
		});
	};

	this.populateModal = function(newHTML) {
		$('#projectModal').dialog('option', 'title', 'Python');
		var tmp = $('<div></div>');
		tmp.html(newHTML);
		var firstBug = $('.odd', tmp).first();
		var lastUpdated = $('.date', firstBug).first()[0];
		var lastUpdatedText = $(lastUpdated).text();
		var innerDialog = '<p><b>Last Updated:</b> '+lastUpdatedText+'</p>';
		stopLoad();
		$('#projectModal').append(innerDialog);
	};	
};
PythonWrapper.prototype = Object.create(APIWrapper.prototype);

//ID-Api IdMapping
var IdMapping = {
	//No Object for Github since they all work the same
	89: GithubWrapper,
	66: {  //Bugzilla
		103: BugzillaMozilla
	},
	91: {  //Jira
		264: JiraMifos,
		242: JiraCyanogenmod
	},
	64: {  //Google - No API (either scrape or use source code)
		36: SympyWrapper // example of just using source code
	},
	86: {  //Launchpad
		215: HorizonLaunchpad,
		274: HeatLaunchpad,
		208: UbuntuQualityManualTestcasesLaunchpad,
		209: UbuntuQualityAutopilotTestcasesLaunchpad,
		250: StratagusLaunchpad
	},
	72: {
		31: OpenhatchWrapper,
		93: PythonWrapper
	}
};

//Function to create APIWrapper
var createAPIWrapper = function(tracker_type, tracker_id, link) {
	var currentWrapper;
	if (typeof IdMapping[tracker_type] == 'object') {
		currentWrapper = 
			new IdMapping[tracker_type][tracker_id](tracker_type, tracker_id, link);
	} else {
		currentWrapper = 
			new IdMapping[tracker_type](tracker_type, tracker_id, link);
	}
	//If API Data is not in cache, execute it
	if (!isInDataCache(tracker_id)) {
		currentWrapper.executeAPI();
	} else { //Else use current data for the job
		$('#projectModal').dialog('open');
		currentWrapper.populateModal.apply(this, DataCache[tracker_id]);
	}
};

//Get difference between a date and right now in years, months, days
//Note: this is not exact (leap years, etc), but it's pretty good
//We could include a library like Moment.js or Date.js
var getAge = function(dateString) {
    var today = new Date();
    var startDate = new Date(dateString);
    var years = Math.floor((today - startDate) / 
    	(1000*60*60*24*365.25));
    var totalMonths = Math.floor((today - startDate)*12 / 
    	(1000*60*60*24*365.25));
    var months = totalMonths - 12*years;
    var totalDays = Math.floor((today - startDate) / 
    	(1000*60*60*24));
    var days = totalDays - 365*years - (365.25/12)*months;
    return [years, months, days];
};

//Generate Empty Modal
var populateEmptyModal = function() {
	$('#projectModal').dialog('option', 'title', 'No Project Data');
	var innerDialog = "<p>Sorry! This project's API has not been added yet!</p>";
	$('#projectModal').append(innerDialog);
	$('#projectModal').dialog('open');
	stopLoad();
};

//Handle AJAX error - the modal is already open
var populateErrorModal = function(textStatus) {
	$('#projectModal').dialog('option', 'title', 'Error!');
	var innerDialog = "<p>There was an error!</p>"+
					  "<p>The error was: "+textStatus;
	stopLoad();
	$('#projectModal').append(innerDialog);
};

//Handle AJAX timeout - the modal is already open
var populateTimeoutModal = function() {
	$('#projectModal').dialog('option', 'title', 'Timeout!');
	var innerDialog = "<p>Sorry! We took to long to load this!</p>"+
					  "<p>Maybe try again?</p>"+
					  "<p>If this happens repeatedly, there's probably something "+
					  "wrong with this project's API</p>";
	stopLoad();
	$('#projectModal').append(innerDialog);
};

//Loading wheel animations
var startLoad = function() {
	$('#loadingWheel').show();
};

var stopLoad = function() {
	$('#loadingWheel').hide();
};

$(function() {
	//Define Project Modal
	$("#projectModal").dialog({
		autoOpen: false,
		modal: true,
		width: "40%",
		open: function() {
			$("#projectModal").dialog("option", "position", {
				my: "center", 
				at: "center", 
				of: window});
			$(".ui-widget-overlay").css({
            	opacity: .3,
            	filter: "Alpha(Opacity=30)",
            	background: "black",
        	});
        	startLoad();
            $('.ui-widget-overlay').bind('click',function(){
                $('#projectModal').dialog('close');
            });
        },
        close: function(event, ui) {
        	var wheel = $("#loadingWheel");
        	$("#projectModal").html(wheel);
        	$('#projectModal').dialog('option', 'title', '');
        }
	});

	//Attach listeners to button
	$('.project_data_button').click(function() {
		var tracker_type = $(this).data("tracker");
		var tracker_id = $(this).data("id");
		var	link = $(this).data("link");
		if (IdMapping.hasOwnProperty(tracker_type)) {
			if (typeof IdMapping[tracker_type] != 'object') {
				createAPIWrapper(tracker_type, tracker_id, link);
			} else {
				if (IdMapping[tracker_type].hasOwnProperty(tracker_id)) {
					createAPIWrapper(tracker_type, tracker_id, link);
				} else {
					console.log("Tracker_type:"+tracker_type+
									", Tracker_id:"+tracker_id+
									" not in IdMapping yet");
					populateEmptyModal();
				}
			}
		}
		else {
			console.log("Tracker_type:"+tracker_type+
							", Tracker_id:"+tracker_id+
							" not in IdMapping yet");
			populateEmptyModal();
		}
	});

	//When window resizes, keep modal in the middle
	$(window).resize(function() {
    	$("#projectModal").dialog("option", "position", {
    		my: "center", 
    		at: "center", 
    		of: window});
	});
});
