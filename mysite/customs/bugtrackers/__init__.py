# This file is part of OpenHatch.

#####################################################
########## THIS IS DEPRECATED #######################
########## WE INTEND TO MOVE THIS CODE ##############
########## INTO A SUBCLASS OF BUGPARSER OR ##########
########## BUGIMPORTER. IT WILL GO AWAY WITHIN ######
########## A MONTH OR SO. ###########################
########## INFO: http://lists.openhatch.org/pipermail/devel/2011-November/002466.html #

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

# This is an extremely skeletal bug tracker-like class,
# used by the mysite.search.tests.BugCanRefreshItself test.
class BugTracker(object):
    def refresh_one_bug(self, bug):
        pass
