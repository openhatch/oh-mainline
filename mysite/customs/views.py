# This file is part of OpenHatch.
# Copyright (C) 2010, 2011 Jack Grigg
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

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
import django.shortcuts

from reversion import revision

import mysite.base.decorators
import mysite.customs.forms
import mysite.customs.models

from mysite.customs.core_bugimporters import all_trackers

# Lists all the stored trackers of a selected type (Bugzilla, Trac etc.)
@mysite.base.decorators.view
def list_trackers(request, tracker_types_form=None):
    data = {}
    if request.POST:
        tracker_types_form = mysite.customs.forms.TrackerTypesForm(
                request.POST, prefix='list_trackers')
        if tracker_types_form.is_valid():
            tracker_type = tracker_types_form.cleaned_data['tracker_type']
        else:
            tracker_type = 'bugzilla'
    else:
        tracker_type = 'bugzilla'
    if tracker_type in all_trackers:
        trackers = all_trackers[tracker_type]['model'].all_trackers.all()
    else:
        trackers = []
    data['tracker_type'] = tracker_type
    data['trackers'] = trackers
    notification_id = request.GET.get('notification_id', None)
    notifications = {
            'add-success': 'Bugtracker successfully added! Bugs from this tracker should start appearing within 24 hours.',
            'edit-success': 'Bugtracker successfully edited! New settings should take effect within 24 hours.',
            'delete-success': 'Bugtracker successfully deleted!',
            'tracker-existence-fail': 'Hmm, could not find the requested tracker.',
            'tracker-url-existence-fail': 'Hmm, could not find the requested tracker URL.',
            }
    data['customs_notification'] = notifications.get(notification_id, '')
    if tracker_types_form is None:
        tracker_types_form = mysite.customs.forms.TrackerTypesForm(prefix='list_trackers')
    data['tracker_types_form'] = tracker_types_form
    return (request, 'customs/list_trackers.html', data)

@login_required
def add_tracker(request, tracker_type, tracker_form=None):
    data = {}
    if tracker_type in all_trackers:
        data['tracker_type_pretty'] = all_trackers[tracker_type]['namestr']
        data['action_url'] = reverse(add_tracker_do, args=[tracker_type])

        if tracker_form is None:
            # This is what we'll pass in to the form. By default: blank.
            initial_data = {}

            # If the user passed in a ?project_id= value, then store that in
            # the form's created_for_project values.
            project_id = request.GET.get('project_id', None)
            if project_id is not None:
                try:
                    project = mysite.search.models.Project.objects.get(id=project_id)
                    initial_data['created_for_project'] = project
                except mysite.search.models.Project.DoesNotExist:
                    pass # no biggie

            tracker_form = all_trackers[tracker_type]['form'](
                prefix='add_tracker',
                initial=initial_data)

        data['tracker_form'] = tracker_form

        return mysite.base.decorators.as_view(request, 'customs/add_tracker.html', data, None)
    else:
        # Wrong or no tracker type. Send back to list.
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
@revision.create_on_success
def add_tracker_do(request, tracker_type):
    if tracker_type in all_trackers:
        tracker_form = all_trackers[tracker_type]['form'](
                request.POST, prefix='add_tracker')
        if tracker_form.is_valid():
            tracker_name = tracker_form.cleaned_data['tracker_name']
            # Tracker form is valid, so save away!
            tracker = tracker_form.save()
            # Set the revision meta data.
            revision.user = request.user
            revision.comment = 'Added the %s tracker' % tracker_name
            # Send them off to add some URLs
            return HttpResponseRedirect(reverse(add_tracker_url, args=[tracker_type, tracker.id, tracker_name]))
        else:
            return add_tracker(request,
                    tracker_type=tracker_type,
                    tracker_form=tracker_form)
    else:
        # Wrong or no tracker type. Send back to list.
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
def add_tracker_url(request, tracker_type, tracker_id, tracker_name, url_form=None):
    data = {}
    if tracker_type in all_trackers and (
        url_form or all_trackers[tracker_type].get('urlform', None)):
        if url_form is None:
            try:
                tracker_obj = all_trackers[tracker_type]['model'].all_trackers.get(
                    pk=tracker_id, tracker_name=tracker_name)
                url_obj = all_trackers[tracker_type]['urlmodel'](
                        tracker=tracker_obj)
                url_form = all_trackers[tracker_type]['urlform'](
                        instance=url_obj, prefix='add_tracker_url')
            except all_trackers[tracker_type]['model'].DoesNotExist:
                url_form = all_trackers[tracker_type]['urlform'](prefix='add_tracker_url')
        data['url_form'] = url_form
        data['tracker_name'] = tracker_name
        data['tracker_id'] = tracker_id
        data['cancel_url'] = reverse(edit_tracker, args=[
                tracker_type, tracker_id, tracker_name])
        data['add_more_url'] = reverse(add_tracker_url_do, args=[
                tracker_type, tracker_id, tracker_name])
        data['finish_url'] = reverse(add_tracker_url_do, args=[
                tracker_type, tracker_id, tracker_name])
        data['finish_url'] += '?finished=true'
        return mysite.base.decorators.as_view(request, 'customs/add_tracker_url.html', data, None)
    else:
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
@revision.create_on_success
def add_tracker_url_do(request, tracker_type, tracker_id, tracker_name):
    url_form = None
    if tracker_type in all_trackers:
        tracker_obj = all_trackers[tracker_type]['model'].all_trackers.get(
            pk=tracker_id, tracker_name=tracker_name)
        url_obj = all_trackers[tracker_type]['urlmodel'](
                tracker=tracker_obj)
        url_form = all_trackers[tracker_type]['urlform'](
                request.POST, instance=url_obj, prefix='add_tracker_url')
        if url_form.is_valid():
            # It's valid so save it!
            url_form.save()
            # Set the revision meta data.
            revision.user = request.user
            revision.comment = 'Added URL to the %s tracker' % tracker_name
            # Do they want to add another URL?
            if request.GET.get('finished', None) == 'true':
                return HttpResponseRedirect(reverse(list_trackers) +
                                        '?notification_id=add-success')
            else:
                return HttpResponseRedirect(reverse(add_tracker_url, args=[tracker_type, tracker_id, tracker_name]))
        else:
            return add_tracker_url(
                request,
                tracker_id=tracker_id,
                tracker_type=tracker_type,
                tracker_name=tracker_name,
                url_form=url_form)
    else:
        # Shouldn't get here. Just go back to base.
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
def edit_tracker(request, tracker_type, tracker_id, tracker_name, tracker_form=None):
    data = {}
    if tracker_type in all_trackers:
        try:
            tracker_obj = all_trackers[tracker_type]['model'].all_trackers.get(
                pk=tracker_id, tracker_name=tracker_name)
            if tracker_form is None:
                tracker_form = all_trackers[tracker_type]['form'](
                        instance=tracker_obj, prefix='edit_tracker')
                # Set the initial value for github_url field
                if tracker_type == 'github':
                    tracker_form.initial['github_url'] = tracker_form.instance.get_github_url()
            tracker_urlmodel = all_trackers[tracker_type]['urlmodel']
            tracker_urlform = all_trackers[tracker_type]['urlform']
            if tracker_urlmodel:
                tracker_urls = tracker_urlmodel.objects.filter(
                    tracker=tracker_obj)
            else:
                tracker_urls = []
        except all_trackers[tracker_type]['model'].DoesNotExist:
            return HttpResponseRedirect(reverse(list_trackers) +
                                        '?notification_id=tracker-existence-fail')
        data['tracker_name'] = tracker_name
        data['tracker_id'] = tracker_id
        data['tracker_type'] = tracker_type
        data['tracker_form'] = tracker_form
        data['tracker_urls'] = tracker_urls
        data['tracker_urlmodel'] = tracker_urlmodel
        data['tracker_urlform'] = tracker_urlform
        return mysite.base.decorators.as_view(request, 'customs/edit_tracker.html', data, None)
    else:
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
@revision.create_on_success
def edit_tracker_do(request, tracker_type, tracker_id, tracker_name):
    if tracker_type in all_trackers:
        tracker_obj = all_trackers[tracker_type]['model'].all_trackers.get(
            pk=tracker_id, tracker_name=tracker_name)
        tracker_form = all_trackers[tracker_type]['form'](
                request.POST, instance=tracker_obj, prefix='edit_tracker')
        if tracker_form.is_valid():
            tracker_form.save()
            # Set the revision meta data.
            revision.user = request.user
            revision.comment = 'Edited the %s tracker' % tracker_name
            return HttpResponseRedirect(reverse(list_trackers) +
                                '?notification_id=edit-success')
        else:
            return edit_tracker(request,
                    tracker_type=tracker_type,
                    tracker_id=tracker_id,
                    tracker_name=tracker_name,
                    tracker_form=tracker_form)
    else:
        # Just go back to base.
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
def edit_tracker_url(request, tracker_type, tracker_id, tracker_name, url_id, url_form=None):
    data = {}
    if tracker_type in all_trackers:
        try:
            url_obj = all_trackers[tracker_type]['urlmodel'].objects.get(id=url_id)
            if url_form is None:
                url_form = all_trackers[tracker_type]['urlform'](
                        instance=url_obj, prefix='edit_tracker_url')
        except all_trackers[tracker_type]['urlmodel'].DoesNotExist:
            return HttpResponseRedirect(reverse(list_trackers) +
                    '?notification_id=tracker-url-existence-fail')
        data['tracker_name'] = tracker_name
        data['tracker_id'] = tracker_id
        data['tracker_type'] = tracker_type
        data['url_id'] = url_id
        data['url_form'] = url_form

    data['cancel_url'] = reverse(edit_tracker, args=[tracker_type, tracker_id, tracker_name])
    return mysite.base.decorators.as_view(request, 'customs/edit_tracker_url.html', data, None)

@login_required
@revision.create_on_success
def edit_tracker_url_do(request, tracker_type, tracker_id, tracker_name, url_id):
    url_form = None
    if tracker_type in all_trackers:
        url_obj = all_trackers[tracker_type]['urlmodel'].objects.get(
                id=url_id)
        url_form = all_trackers[tracker_type]['urlform'](
                request.POST, instance=url_obj, prefix='edit_tracker_url')
    if url_form:
        if url_form.is_valid():
            url_form.save()
            # Set the revision meta data.
            revision.user = request.user
            revision.comment = 'Edited URL for the %s tracker' % tracker_name
            return HttpResponseRedirect(reverse(edit_tracker, args=[tracker_type, tracker_id, tracker_name]) +
                                        '?edit-url-success')
        else:
            return edit_tracker_url(request,
                    tracker_type=tracker_type,
                    tracker_id=tracker_id,
                    tracker_name=tracker_name,
                    url_id=url_id,
                    url_form=url_form)
    else:
        # Shouldn't get here. Just go back to base.
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
def delete_tracker(request, tracker_type, tracker_id, tracker_name):
    tracker = django.shortcuts.get_object_or_404(
        all_trackers[tracker_type]['model'].all_trackers,
        pk=tracker_id, tracker_name=tracker_name)

    if request.method == 'POST':
        return delete_tracker_do(
            request, tracker_type, tracker.id, tracker.tracker_name)

    # Else...
    data = {}
    data['tracker_name'] = tracker_name
    data['tracker_type'] = tracker_type
    data['tracker_id'] = tracker_id
    return mysite.base.decorators.as_view(request, 'customs/delete_tracker.html', data, None)

@login_required
@revision.create_on_success
def delete_tracker_do(request, tracker_type, tracker_id, tracker_name):
    if tracker_type in all_trackers:
        tracker = all_trackers[tracker_type]['model'].all_trackers.get(
            pk=tracker_id, tracker_name=tracker_name)
        tracker.delete()
        # Set the revision meta data.
        revision.user = request.user
        revision.comment = 'Deleted the %s tracker' % tracker_name
        # Tell them it worked.
        return HttpResponseRedirect(reverse(list_trackers) +
                        '?notification_id=delete-success')
    else:
        # Shouldn't get here. Just go back to base.
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
def delete_tracker_url(request, tracker_type, tracker_id, tracker_name, url_id):
    data = {}
    if tracker_type in all_trackers:
        data['tracker_name'] = tracker_name
        data['tracker_id'] = tracker_id
        data['tracker_type'] = tracker_type
        data['url_id'] = url_id
        url_obj = all_trackers[tracker_type]['urlmodel'].objects.get(id=url_id)
        data['url'] = url_obj.url
        return mysite.base.decorators.as_view(request, 'customs/delete_tracker_url.html', data, None)
    else:
        # Shouldn't get here. Just go back to base.
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
@revision.create_on_success
def delete_tracker_url_do(request, tracker_type, tracker_id, tracker_name, url_id):
    if tracker_type in all_trackers:
        url_obj = all_trackers[tracker_type]['urlmodel'].objects.get(id=url_id)
        url_obj.delete()
        # Set the revision meta data.
        revision.user = request.user
        revision.comment = 'Deleted URL from the %s tracker' % tracker_name
        # Tell them it worked.
        return HttpResponseRedirect(reverse(edit_tracker, args=[tracker_type, tracker_id, tracker_name]) +
                            '?delete-url-success')
    else:
        return HttpResponseRedirect(reverse(edit_tracker, args=[tracker_type, tracker_name]))
