# -*- coding: utf-8 -*-
from __future__ import absolute_import
# vim: set ai et ts=4 sw=4:

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


# Imports {{{
import mysite.bugsets.views
import mysite.bugsets.models

from mysite.base.tests import TwillTests

from django.core.urlresolvers import reverse
# }}}

class BasicBugsetListTests(TwillTests):
    def test_bugset_names_load(self):
        mysite.bugsets.models.BugSet.objects.create(name="best event")
        mysite.bugsets.models.BugSet.objects.create(name="bestest event")
        url = reverse(mysite.bugsets.views.list_index)
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "best event")
        self.assertContains(response, "bestest event")

    def test_bugset_view_link(self):
        pass

class BasicBugsetViewTests(TwillTests):
    def test_bugset_listview_load(self):
        s = mysite.bugsets.models.BugSet.objects.create(name="test event")
        b = mysite.bugsets.models.AnnotatedBug.objects.create(
            url="http://openhatch.org/bugs/issue995",
        )
        b.bugsets.add(s)
        url = reverse(mysite.bugsets.views.listview_index, kwargs={ 'pk': 1 })
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "test event")
        self.assertContains(response, "http://openhatch.org/bugs/issue995")

