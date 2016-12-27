/*
# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2010 OpenHatch, Inc.
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

if (typeof QUnit == 'undefined') {
    console.log('QUnit not imported.');
}

QUnitRunner = {};
QUnitRunner.ok = function(bool, message) {
    var bool = !!bool;
    if (typeof prefix == 'undefined') { var prefix = ""; }
    test(prefix, function() { ok(bool, message); });
};
QUnitRunner.compare = function(a, b, message) {
    if (typeof prefix == 'undefined') { prefix = ""; }
    test(prefix, function() { equals(a, b, message); });
};
QUnitRunner.testDone = function() {};

StupidRunner = {};
StupidRunner.ok = function(bool, message) {
    var bool = !!bool; //FIXME: Doesn't work in constructive logic.
    if (!bool) { alert("Failed:" + message); }
};
StupidRunner.compare = function(a, b, message) {
    if (a !== b) { alert("Failed: " + a + " != " + b + "; " + message); }
};
StupidRunner.testDone = function() {};

// Pick a test runner here
//tester = fireunit;
//tester = QUnitRunner;
tester = StupidRunner;
