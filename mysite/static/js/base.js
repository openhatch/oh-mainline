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

$(function () {
    $("[rel='tipsy-north']").tipsy({'gravity': 'n'});
    $("[rel='tipsy-east']").tipsy({'gravity': 'e'});
    $("[rel='tipsy-west']").tipsy({'gravity': 'w'});
    $("[rel='tipsy-south']").tipsy({'gravity': 's'});
});
