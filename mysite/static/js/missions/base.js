/*
# This file is part of OpenHatch.
# Copyright (C) 2011 Krzysztof Tarnowski (krzysztof.tarnowski@ymail.com)
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
if (typeof OH === 'undefined') OH = {};
if (typeof OH.Page === 'undefined') OH.Page = {};

$(function() {
  $("#mission-reset-btn").live(
        "click",
        function() {
            $.post(
                OH.Page['post_url'],
                { mission_parts: OH.Page['mission_parts'] },
                function(response) {
                    var items = ['#success-msg', '#next-mission-link'];
                    var len = items.length;
                    var obj = null;

                    for (var i = 0; i < len; i++) {;
                      obj = $(items[i]);
                      if (obj) obj.fadeOut(500);
                    }

		    // Now, update the mission status indicators.
		    $('.tick-progress').removeClass('tick-progress').addClass('cross-progress');
                }
            )
        }
  );
});