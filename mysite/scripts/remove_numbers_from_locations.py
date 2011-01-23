# This file is part of OpenHatch.
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

import re
import mysite
Person = mysite.profile.models.Person

people_with_weird_locations = Person.objects.filter(location_display_name__regex=', [0-9][0-9],')

count = 0
for p in people_with_weird_locations:
    location_pieces = re.split(r', \d\d,', p.location_display_name)
    unweirded_location = ",".join(location_pieces)
    if unweirded_location != p.location_display_name:
        #print p.location_display_name + "->" + unweirded_location
        p.location_display_name = unweirded_location
        print p.user.email + ","
        p.save()
        count += 1
