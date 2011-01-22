/*
# This file is part of OpenHatch.
# Copyright (C) 2009 OpenHatch
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

DefaultText = {
    '$elements': null,
    'init': function() {
        DefaultText.$elements = $("input.default-text");
        DefaultText.bindFocusHandler();
        DefaultText.bindBlurHandler();
        DefaultText.$elements.trigger('focus');
        DefaultText.$elements.trigger('blur');
    },  
    'bindFocusHandler': function() {
        DefaultText.$elements.focus(DefaultText.focusHandler);
    },
    'focusHandler': function() {
        if ($(this).val() == $(this)[0].title) {
            $(this).removeClass("default-text-active");
            $(this).val("");
        }
    },
    'bindBlurHandler': function() {
        DefaultText.$elements.blur(DefaultText.blurHandler);
    },
    'blurHandler': function() {
        if ($(this).val() == "") {
            $(this).addClass("default-text-active");
            $(this).val($(this)[0].title);
        }
    }
};
$(DefaultText.init);
