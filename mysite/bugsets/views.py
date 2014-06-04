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
import mysite.bugsets.models

from django.shortcuts import render
# }}}


def list_index(request):
    bugsets = mysite.bugsets.models.BugSet.objects.all()
    context = {
        'bugsets': bugsets,
    }
    return render(request, 'list_index.html', context)


def listview_index(request, pk, slug):
    bugset = mysite.bugsets.models.BugSet.objects.get(pk=pk)
    bugs = bugset.bugs.all()
    context = {
        'bugset': bugset,
        'bugs': bugs,
    }
    return render(request, 'listview_index.html', context)
