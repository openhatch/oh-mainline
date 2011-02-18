/*
# This file is part of OpenHatch.
# Copyright (C) 2011 Krzysztof Tarnowski (krzysztof.tarnowski@ymail.com)
# Copyright (C) 2011 OpenHatch, Inc.
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

/* Recommended bugs box */
$(function() {
    if ($('#ajax-loader-rec-bugs').size() > 0) {
        $.getJSON(
            '/+profile/bug_recommendation_list_as_template_fragment',
            function(response) {
                var elem = null;

                if (response.result == 'OK') {
                    var bug_rec = $('#bug-recommendations');
                    bug_rec.html(response.html);
                    elem = bug_rec;
                } else if (response.result == 'NO_BUGS'){
                    elem = $('#volunteer-opportunities');
                } else {
                    $('#bug-recommendations').html('An error occured');
                    elem = $('#bug-recommendations');
                }

                $('#ajax-loader-rec-bugs').fadeOut();
                elem.fadeIn();
            }
        );
    }
});
