/*
# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2009 Karen Rustad
# Copyright (C) 2009, 2010 OpenHatch, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

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

$.fn.changeTipsyMessageText = function (msg) {
    // Note that this doesn't respect tipsy options

    // Change the tipsy text, which is stored in the title attribute
    this.attr('title', msg);

    // If a tipsy is currently open, update its text
    var $tipsy = this.getTipsy();
    if (typeof $tipsy !== 'undefined') {
        $tipsy.find('.tipsy-inner').text(msg);
    }
};

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
