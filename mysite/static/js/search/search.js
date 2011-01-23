/*
# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
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

$.fn.toggleExpanded = function() {
    this.toggleClass('expanded');
    return this;
};

SearchResults = {}

SearchResults.bindEventHandlers = function () {

    console.log('SearchResults.bindEventHandlers');

    $('.project__name, .first-line').click(function () {
            $result = $(this.parentNode.parentNode);
            $result.toggleExpanded();
            // don't use this, so that links work return false;
            });

    $('.show-details').click(function () {
            $result = $(this.parentNode.parentNode.parentNode.parentNode);
            $result.toggleExpanded();
            return false;
            });

    $('#expand-all-link').click(function() {
            $('#results li').addClass('expanded');
            return false;
            });

    $('#collapse-all-link').click(function() {
            $('#results li').removeClass('expanded');
            return false;
            });

}

/* vim: set ai ts=4 sts=4 et sw=4: */
