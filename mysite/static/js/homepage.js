/*
# This file is part of OpenHatch.
# Copyright (C) 2009 OpenHatch, Inc.
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

// Depends on jQuery

if (typeof $ == 'undefined') {
    alert('Oops, somebody forgot to import jQuery (a Javascript library)!');
}

var abstractTabLinkClickHandler = function (link) {
    $('.tab-links a').addClass('my-tab-is-hidden');
    $(link).removeClass('my-tab-is-hidden');
    $('.tab').addClass('invisible_if_js');
    var tab_selector = $(link).attr('tab_selector');
    $(tab_selector).removeClass('invisible_if_js');
    return false;
};

var tabLinkClickHandler = function() {
    return abstractTabLinkClickHandler(this);
};

var bindTabEventHandlers = function () {
    $('.tab-links a').click(tabLinkClickHandler);
};

var prepareTabs = function () {
    // Hide all tabbed panels except the first.
    $('.tab:not(:eq(0))').addClass('invisible_if_js');
    $('.tab-links li:not(:first-child) a').addClass('my-tab-is-hidden');
// Check if we want to enable a particular tab.
    var hash = document.location.href.split('#')[1];
    if (hash) {
        if (hash.substr(0, 4) == 'tab=') {
            tab_name = hash.substr(4);
            /* Find the right <a> */
            var link = $("a[tab_selector=#" + 
                    tab_name + "]")[0];
            abstractTabLinkClickHandler(link);
        }
    }
}

// Show or hide the normal, non-OpenID login form.
ToggleNormalLoginForm = {
    '$toggleLink': null,
    '$form': null,
    '$verb': null,
    'toggleForm': function () {
        var isLoginFormHidden = (ToggleNormalLoginForm.$form.css('display') == 'none');
        var methodName = isLoginFormHidden ? 'show' : 'hide';
        ToggleNormalLoginForm.$form[methodName]();
        ToggleNormalLoginForm.$verb.text(isLoginFormHidden ? 'Hide' : 'Show');
        return false;
    },
    'initialize': function () {
        ToggleNormalLoginForm.$toggleLink = $('#toggleNormalLogin').click(
                ToggleNormalLoginForm.toggleForm);
        ToggleNormalLoginForm.$form = $('#normal_login_form').hide();
        ToggleNormalLoginForm.$verb = $('#toggleNormalLogin .verb');
    }
};

$(bindTabEventHandlers);
$(prepareTabs);
$(ToggleNormalLoginForm.initialize);
