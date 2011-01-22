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

from mysite.profile.models import Citation

for citation in Citation.objects.all().order_by('pk'):
    citation.ignored_due_to_duplicate = False
    citation.save()
    older_duplicates = [dupe for dupe in
            Citation.objects.filter(portfolio_entry=citation.portfolio_entry)
            if (dupe.date_created <= citation.date_created) 
            and (dupe.pk != citation.pk)
            and (dupe.summary == citation.summary)]
    if older_duplicates:
        citation.ignored_due_to_duplicate = True
    citation.save()

