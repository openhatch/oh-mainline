# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010 John Stumpo
# Copyright (C) 2011 Krzysztof Tarnowski (krzysztof.tarnowski@ymail.com)
# Copyright (C) 2010, 2011 OpenHatch, Inc.
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

import django.views.generic

class WindowsMissionPage(django.views.generic.TemplateView):
    def get_context_data(self):
        data = super(WindowsMissionPage, self).get_context_data()
        data.update({
                'this_mission_page_short_name': self.this_mission_page_short_name,
                'mission_name': 'Finding the command line on Windows'})
        return data

class WindowsMainPage(WindowsMissionPage):
    this_mission_page_short_name = 'What we recommend and why'
    template_name = 'missions/windows-setup/about.html'
