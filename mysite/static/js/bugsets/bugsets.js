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

var error_count = 0;
var ERROR_COUNT_THRESHOLD = 6;

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
            error_count++;
            if(error_count > ERROR_COUNT_THRESHOLD) {
                $("div#error-notification").html("You might need to check your internet connection and reload the page.\n (Could not reach server when refreshing page data.)");
            }
        },

        success: updateHTML
    });
}

function updateHTML(response) {
    // Don't update fields with empty values
    $("div#error-notification").html("");
    // reset error_count
    error_count = 0;
    if (response.new_html == '') {
        return;
    }

    node = $('inplaceeditform[obj_id=' + response.obj_id + '][field_name=' +
        response.field_name + ']').parent()

    // Two nodes match when field_name='status', so we need a 'foreach' here
    $(node).each(function () {
        ipe_tag = $(this).find('inplaceeditform').detach()
        $(this).html(response.new_html)
        $(this).append(ipe_tag)
    })
}

function runOnInterval() {
    setTimeout(runOnInterval, 5000);  // 5s = 5000ms
    updateFields();
}

// Delicious recursive call
$(runOnInterval());


/* vim: set ai ts=4 sts=4 et sw=4: */
