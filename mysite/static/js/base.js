if (typeof console == "undefined") {
    console = {};
    console.log = function() {};
    console.debug = function() {};
    console.info = function() {};
}

fireunitEnabled = true;
if (typeof fireunit == "undefined") {
    fireunitEnabled = false;
    fireunit = {};
    fireunit.ok = function() {};
    fireunit.testDone = function() {};
}

// Thanks to
// Damir's comment on "Javascript - array.contains(obj)"
// <http://stackoverflow.com/questions/237104/javascript-array-containsobj/237176#237176>
Array.prototype.contains = function(obj) {
    var i = this.length;
    while (i--) {
        if (this[i] === obj) {
            return true;
        }
    }
    return false;

}

// Thanks to
// "Escaping regular expression characters in Javascript"
// by Simon Willison, posted on 20th January 2006.
// <http://simonwillison.net/2006/Jan/20/escape/>
RegExp.escape = function(text) {
    if (!arguments.callee.sRE) {
        var specials = [
            '/', '.', '*', '+', '?', '|',
            '(', ')', '[', ']', '{', '}', '\\'
                ];
        arguments.callee.sRE = new RegExp(
                '(\\' + specials.join('|\\') + ')', 'g'
                 );
                }
                return text.replace(arguments.callee.sRE, '\\$1');
};

$.fn.getTipsy = function() {
    return $.data(this.get(0), 'active.tipsy');
}

$.fn.toggleDisplay = function() { 
    var what_to_do = this.is(':visible') ? 'hide' : 'show';
    this[what_to_do]();
}

$(function () {
    $("input[rel='hint']").hint();
    $("a[rel='facebox']").facebox();
});

ShowMoreProjects = {
    'init': function () {
        $('#show_more_projects').click(function () {
            $(this).hide();
            $('.archived').show();
            return false;
        });
    }
};
