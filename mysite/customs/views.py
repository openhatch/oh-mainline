from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

import mysite.base.decorators
import mysite.customs.forms
import mysite.customs.models

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
    if tracker_type == 'bugzilla':
        trackers = mysite.customs.models.BugzillaTracker.all_trackers.all()
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
@mysite.base.decorators.view
def add_tracker(request, tracker_type=None, tracker_form=None):
    data = {}
    if tracker_type == 'bugzilla':
        data['action_url'] = reverse('add_tracker_specific_do', args=[tracker_type])
        if tracker_form is None:
            tracker_form = mysite.customs.forms.BugzillaTrackerForm(prefix='add_tracker')
    else:
        # Wrong or no tracker type
        data['action_url'] = reverse('add_tracker_choose_type_do')
        if tracker_form is None:
            tracker_form = mysite.customs.forms.TrackerTypesForm(prefix='add_tracker')
    data['tracker_form'] = tracker_form
    return (request, 'customs/add_tracker.html', data)

@login_required
def add_tracker_do(request, tracker_type=None):
    if tracker_type == 'bugzilla':
        bugzilla_tracker_form = mysite.customs.forms.BugzillaTrackerForm(
                request.POST, prefix='add_tracker')
        if bugzilla_tracker_form.is_valid():
            bugzilla_tracker_form.save()
            return HttpResponseRedirect(reverse(add_tracker_url, args=[tracker_type]) +
                                        '?project_name=' +
                                        bugzilla_tracker_form.cleaned_data['project_name'])
        else:
            return add_tracker(request,
                    tracker_type=tracker_type,
                    tracker_form=bugzilla_tracker_form)
    else:
        tracker_types_form = mysite.customs.forms.TrackerTypesForm(
                request.POST, prefix='add_tracker')
        if tracker_types_form.is_valid():
            tracker_type = tracker_types_form.cleaned_data['tracker_type']
            return HttpResponseRedirect(reverse('add_tracker_specific', args=[tracker_type]))
        else:
            return add_tracker(request,
                    tracker_form=tracker_types_form)

@login_required
@mysite.base.decorators.view
def add_tracker_url(request, tracker_type, project_name, url_form=None):
    data = {}
    if tracker_type == 'bugzilla':
        if url_form is None:
            if project_name:
                try:
                    bugzilla_tracker = mysite.customs.models.BugzillaTracker.all_trackers.get(
                            project_name=project_name)
                    bugzilla_url = mysite.customs.models.BugzillaUrl(
                            bugzilla_tracker=bugzilla_tracker)
                    url_form = mysite.customs.forms.BugzillaUrlForm(
                            instance=bugzilla_url, prefix='add_tracker_url')
                except mysite.customs.models.BugzillaTracker.DoesNotExist:
                    url_form = mysite.customs.forms.BugzillaUrlForm(prefix='add_tracker_url')
            else:
                url_form = mysite.customs.forms.BugzillaUrlForm(prefix='add_tracker_url')
        data['url_form'] = url_form
    data['add_more_url'] = reverse(add_tracker_url_do, args=[tracker_type, project_name])
    data['finish_url'] = reverse(add_tracker_url_do, args=[tracker_type, project_name])
    data['finish_url'] += '?finished=true'
    return (request, 'customs/add_tracker_url.html', data)

@login_required
def add_tracker_url_do(request, tracker_type, project_name):
    url_form = None
    if tracker_type == 'bugzilla':
        url_form = mysite.customs.forms.BugzillaUrlForm(
                request.POST, prefix='add_tracker_url')
    if url_form:
        if url_form.is_valid():
            url_form.save()
            if request.GET.get('finished', None) == 'true':
                return HttpResponseRedirect(reverse(list_trackers) +
                                        '?notification_id=add-success')
            else:
                return add_tracker_url(request,
                        tracker_type=tracker_type)
        else:
            return add_tracker_url(request,
                    tracker_type=tracker_type,
                    project_name=project_name,
                    url_form=url_form)
    else:
        # Shouldn't get here. Just go back to base.
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
def edit_tracker(request, tracker_type, project_name, tracker_form=None):
    data = {}
    if tracker_type == 'bugzilla':
        try:
            bugzilla_tracker = mysite.customs.models.BugzillaTracker.all_trackers.get(
                    project_name=project_name)
            if tracker_form is None:
                tracker_form = mysite.customs.forms.BugzillaTrackerForm(
                        instance=bugzilla_tracker, prefix='edit_tracker')
            tracker_urls = mysite.customs.models.BugzillaUrl.objects.filter(
                    bugzilla_tracker=bugzilla_tracker)
        except mysite.customs.models.BugzillaTracker.DoesNotExist:
            return HttpResponseRedirect(reverse(list_trackers) +
                                        '?notification_id=tracker-existence-fail')
        data['project_name'] = project_name
        data['tracker_type'] = tracker_type
        data['tracker_form'] = tracker_form
        data['tracker_urls'] = tracker_urls
        return mysite.base.decorators.as_view(request, 'customs/edit_tracker.html', data, None)
    else:
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
def edit_tracker_do(request, tracker_type, project_name):
    if tracker_type == 'bugzilla':
        bugzilla_tracker = mysite.customs.models.BugzillaTracker.all_trackers.get(
                project_name=project_name)
        tracker_form = mysite.customs.forms.BugzillaTrackerForm(
                request.POST, instance=bugzilla_tracker, prefix='edit_tracker')
        if tracker_form.is_valid():
            tracker_form.save()
            return HttpResponseRedirect(reverse(list_trackers) +
                                '?notification_id=edit-success')
        else:
            return edit_tracker(request,
                    tracker_type=tracker_type,
                    project_name=project_name,
                    tracker_form=tracker_form)
    else:
        # Just go back to base.
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
def edit_tracker_url(request, tracker_type, project_name, url_form=None):
    data = {}
    url = request.GET.get('url', None)
    if tracker_type == 'bugzilla':
        if url_form is None:
            if url:
                try:
                    bugzilla_url = mysite.customs.models.BugzillaUrl.objects.get(url=url)
                    url_form = mysite.customs.forms.BugzillaUrlForm(
                            instance=bugzilla_url, prefix='edit_tracker_url')
                except mysite.customs.models.BugzillaUrl.DoesNotExist:
                    return HttpResponseRedirect(reverse(list_trackers) +
                            '?notification_id=tracker-url-existence-fail')
            else:
                return HttpResponseRedirect(reverse(list_trackers))
        data['project_name'] = project_name
        data['tracker_type'] = tracker_type
        data['url'] = url
        data['url_form'] = url_form

    return mysite.base.decorators.as_view(request, 'customs/edit_tracker_url.html', data, None)

@login_required
def edit_tracker_url_do(request, tracker_type, project_name):
    url_form = None
    old_url = request.GET.get('url', None)
    if tracker_type == 'bugzilla':
        url_form = mysite.customs.forms.BugzillaUrlForm(
                request.POST, prefix='edit_tracker_url')
        tracker_url = mysite.customs.models.BugzillaUrl.objects.get(
                url=old_url)
    if url_form:
        if url_form.is_valid():
            tracker_url.url = url_form.cleaned_data['url']
            tracker_url.save()
            return HttpResponseRedirect(reverse(edit_tracker, args=[tracker_type]) +
                                '?project_name=' + project_name + '&edit-url-success')
        else:
            return edit_tracker_url(request,
                    tracker_type=tracker_type,
                    project_name=project_name,
                    url_form=url_form)
    else:
        # Shouldn't get here. Just go back to base.
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
@mysite.base.decorators.view
def delete_tracker(request, tracker_type, project_name):
    data = {}
    data['project_name'] = project_name
    data['tracker_type'] = tracker_type
    return (request, 'customs/delete_tracker.html', data)

@login_required
def delete_tracker_do(request, tracker_type, project_name):
    if tracker_type == 'bugzilla':
        tracker = mysite.customs.models.BugzillaTracker.all_trackers.get(
                project_name=project_name)
        tracker.delete()
        return HttpResponseRedirect(reverse(list_trackers) +
                        '?notification_id=delete-success')
    else:
        # Shouldn't get here. Just go back to base.
        return HttpResponseRedirect(reverse(list_trackers))

@login_required
@mysite.base.decorators.view
def delete_tracker_url(request, tracker_type, project_name):
    data = {}
    url = request.GET.get('url', None)
    data['project_name'] = project_name
    data['tracker_type'] = tracker_type
    data['url'] = url
    return (request, 'customs/delete_tracker_url.html', data)

@login_required
def delete_tracker_url_do(request, tracker_type, project_name):
    project_name = request.GET.get('project_name', None)
    url = request.GET.get('url', None)
    if tracker_type == 'bugzilla':
        tracker_url = mysite.customs.models.BugzillaUrl.objects.get(url=url)
        tracker_url.delete()
        return HttpResponseRedirect(reverse(edit_tracker, args=[tracker_type, project_name]) +
                            '?delete-url-success')
