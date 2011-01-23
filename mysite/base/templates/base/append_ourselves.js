/*
# This file is part of OpenHatch.
# Copyright (C) 2009 OpenHatch, Inc.
# Copyright (C) 2010 John Stumpo
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

var in_string = {{ in_string|safe }};

var thisScript = /openhatch-widget.js/;
var theScripts = document.getElementsByTagName('script');
for (var i = 0 ; i < theScripts.length; i++) {
    if(theScripts[i].src.match(thisScript)) {
        var inForm = false;
        var currentNode = theScripts[i].parentNode;
        while (currentNode != null) {
            if (currentNode.nodeType == 1) {
                if (currentNode.tagName.toLowerCase() == 'form') {
                    inForm = true;
                    break;
                }
            }
            /* always */
            currentNode = currentNode.parentNode;
        }
        
        if (inForm) {
            /* if we are inside a form, we do not want to create
               another form tag. So replace our FORM tag with
               a DIV.
            */
            in_string = in_string.replace('<form ', '<div ');
            in_string = in_string.replace('</form>', '</div>');
        }
        var my_div = document.createElement('div');
        my_div.innerHTML = in_string;

        /* Hack alert: If we're in an XHTML document being served as
           application/xhtml+xml, we need to transplant the CSS into
           the page header for things to work correctly... */
        var my_style = my_div.getElementsByTagName('style')[0];
        var css_code = my_style.textContent;
        my_div.removeChild(my_style);

        var new_style = document.createElement('style');
        new_style.setAttribute('type', 'text/css');
        new_style.appendChild(document.createTextNode(css_code));
        var page_head = document.getElementsByTagName('head')[0];
        page_head.appendChild(new_style);

        theScripts[i].parentNode.insertBefore(my_div, theScripts[i]);
        theScripts[i].parentNode.removeChild(theScripts[i]);
        break;
    }
}
