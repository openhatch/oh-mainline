# This file is part of OpenHatch.
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

from mysite.search.models import Project, Bug, Buildhelper, BuildhelperStep
from django.contrib import admin


class BuildhelperStepInline(admin.StackedInline):
    model = BuildhelperStep
    extra = 1


class BuildhelperAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['project']}),
        (None, {'fields': ['default_frustration_handler']})
    ]
    inlines = [BuildhelperStepInline]

admin.site.register(Project)
admin.site.register(Bug)
admin.site.register(Buildhelper, BuildhelperAdmin)
