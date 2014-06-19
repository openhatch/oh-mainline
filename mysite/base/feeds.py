# This file is part of OpenHatch.
# Copyright (C) 2011 Jack Grigg
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

from django.contrib.syndication.views import Feed, FeedDoesNotExist
from django.core.exceptions import ObjectDoesNotExist
from django.utils.feedgenerator import Atom1Feed
from mysite.profile.models import Person
from mysite.search.models import Answer, WannaHelperNote


class RecentActivityFeed(Feed):
    feed_type = Atom1Feed
    title = "Recent activity"
    subtitle = "Recent activity on OpenHatch"
    link = "/"

    def items(self):
        feed_items = list(Answer.objects.order_by('-modified_date')[:15])
        feed_items.extend(
            WannaHelperNote.objects.order_by('-modified_date')[:15])
        feed_items.sort(key=lambda x: x.modified_date, reverse=True)
        return feed_items[:15]
