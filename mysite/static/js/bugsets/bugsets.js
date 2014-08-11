/*
# This file is part of OpenHatch.
# Copyright (C) 2014 Elana Hashman
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

function runOnInterval() {
    // maybe every 15s
}

function updateFields() {
    $('inplaceeditform').each(function () {
        getNewValue($(this).attr('obj_id'), $(this).attr('field_name'))
    })
}

function getNewValue(obj_id, field_name) {
    $.ajax({
        url: "/bugsets/api/",
        data: {
            obj_id: obj_id,
            field_name: field_name
        },
        type: "GET",
        async: true,
        dataType: "json",

        // FIXME: This pops up an alert for all the fields, which is bad
        error: function () {
            alert("You might need to check your internet connection and reload the page.\n (Could not reach server when refreshing page data.)");
        },

        success: updateHTML
    });
}

function updateHTML(response) {
    // stash the tag away
    node = $('inplaceeditform[obj_id=' + response.obj_id + '][field_name=' + 
        response.field_name + ']').parent()
    ipe_tag = node.find('inplaceeditform').detach()
    node.html(response.new_html)
    node.append(ipe_tag)
}

/* vim: set ai ts=4 sts=4 et sw=4: */
