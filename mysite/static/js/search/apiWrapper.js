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
		$("#projectModal").attr('title', this.repo);
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

$(function() {
	//Define Project Modal
	$("#projectModal").dialog({
		autoOpen: false,
		modal: true,
		zIndex: 9999,
		open: function(){
			$(".ui-widget-overlay").css({
            	opacity: .3,
            	filter: "Alpha(Opacity=30)",
            	background: "black",
            	position: "fixed",
        	});
            $('.ui-widget-overlay').bind('click',function(){
                $('#projectModal').dialog('close');
            });
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
});

//When window resizes, keep modal in the middle
$(window).resize(function() {
    $("#projectModal").dialog("option", "position", {my: "center", at: "center", of: window});
});