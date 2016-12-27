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
from mysite.bugsets.forms import BugsForm

import json
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
# }}}


def main_index(request):
    bugsets = mysite.bugsets.models.BugSet.objects.all()
    context = {
        'bugsets': bugsets,
    }
    return render(request, 'main_index.html', context)


def list_index(request, pk, slug):
    bugset = mysite.bugsets.models.BugSet.objects.get(pk=pk)
    bugs = bugset.bugs.all()
    context = {
        'bugset': bugset,
        'bugs': bugs,
    }
    return render(request, 'list_index.html', context)


@login_required
def create_index(request, pk=None, slug=None):
    context = {}

    # Edit form
    if pk:
        s = mysite.bugsets.models.BugSet.objects.get(pk=pk)
        bugs = s.bugs.all()

        # Submit edit form
        if request.method == 'POST':
            form = BugsForm(data=request.POST, pk=s.pk)
            if form.is_valid():
                form.update()
                return HttpResponseRedirect(form.object.get_edit_url())
        else:
            form = BugsForm(data=None, pk=s.pk)

        context = {
            'form': form,
            'bugs': bugs,
            'bugset': s,
        }

        return render(request, 'edit_index.html', context)

    # Submit create form
    if request.method == 'POST':
        form = BugsForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(form.object.get_edit_url())
        # else:
        context['form'] = form

    # Blank create form
    if 'form' not in context:
        context['form'] = BugsForm()
    return render(request, 'create_index.html', context)


def api_index(request):
    data = request.GET

    try:
        b = mysite.bugsets.models.AnnotatedBug.objects.get(
            pk=data['obj_id'])

        return HttpResponse(json.dumps({
            'obj_id': data['obj_id'],
            'field_name': data['field_name'],
            'new_html': b.get_status_display()
            if data['field_name'] == 'status'
            else getattr(b, data['field_name']),
        }))

    except ObjectDoesNotExist:
        return HttpResponse(json.dumps({
            'error': 'Object does not exist!',
        }))

    except Exception:
        return HttpResponse(json.dumps({
            'error': 'Unknown error',
        }))
