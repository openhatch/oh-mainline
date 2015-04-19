//API Wrapper for Client
var APIWrapper = function(id) {
	this.id = id;
};

APIWrapper.prototype.toString = function() {
	return this.id;
};

//Github Wrapper
var GithubWrapper = function(id) {
	APIWrapper.call(id);
};

GithubWrapper.prototype = new APIWrapper();




//Attach listeners to button
$('.project_data_button').click(function() {
	console.log(this);
	alert(this);
});