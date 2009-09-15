# -*- coding: utf-8 -*-

from django.http import HttpResponse, \
        HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response
import mysite.account
import mysite.account.forms
from django_authopenid.forms import OpenidSigninForm
import simplejson
from django.template import RequestContext, loader, Context
from django.core.urlresolvers import reverse
import mysite.profile as profile
from mysite.profile.views import display_person_web
import feedparser
import lxml.html
from django.core.cache import cache

def homepage(request, signup_form=None,
        invitation_request_form=None, initial_tab_open='request_invitation'):

    if request.user.is_authenticated():
        return landing_page(request)

    openid_signin_form = OpenidSigninForm()

    signup_notification = login_notification = notification_id = None
    if request.GET.get('msg', None) == 'ciao':
        login_notification = "You've been logged out. Thanks for dropping in!"
        notification_id = 'ciao'
    # FIXME: I think the control block below is dead.
    elif request.GET.get('msg', None) == 'username_taken':
        signup_notification = "Your chosen username is already taken. Try another one."
        notification_id = 'username_taken'

    if not signup_form:
        signup_form = mysite.account.forms.UserCreationFormWithEmail()

    if not invitation_request_form:
        invitation_request_form = mysite.account.forms.InvitationRequestForm()

    data = {
            'notification_id': notification_id,
            'login_notification': login_notification,
            'signup_notification': signup_notification,
            'openid_signin_form': openid_signin_form,
            'signup_form': signup_form,
            'invitation_request_form': invitation_request_form,
            }

    data['initial_tab_open'] = initial_tab_open
    data['interrogative_grunt'] = [u'Hm?', u'Huh?', u'Quoi?', u'¿Que?', u'What‽']

    invitation_requested_for = request.GET.get("invitation_requested_for", None)
    if invitation_requested_for:
        data['invitation_requested_for'] = invitation_requested_for
        data['invitation_success'] = True
        data['initial_tab_open'] = "request_invitation"

    return render_to_response('base/homepage.html', data, context_instance=RequestContext(request))

def _blog_entries():
    # Add blog data here
    parsed = feedparser.parse('http://openhatch.org/blog/feed/atom/')
    for entry in parsed.entries:
        entry.unicode_text = lxml.html.fragments_fromstring(entry.summary)[0]
    return parsed.entries

def cached_blog_entries():
    key_name = 'blog_entries'
    entries = cache.get(key_name)
    if entries is None:
        entries = _blog_entries()
        # cache it for 30 minutes
        cache.set(key_name, entries, 30 * 60)
    return entries

def landing_page(request):
    data = profile.views.get_personal_data(request.user.get_profile())
    data['the_user'] = request.user

    data['entries'] = cached_blog_entries()

    return render_to_response('base/landing.html', data)

def page_to_js(request):
    # FIXME: In the future, use:
    # from django.template.loader import render_to_string
    # to generate html_doc
    html_doc = "<strong>zomg</strong>"
    encoded_for_js = simplejson.dumps(html_doc)
    # Note: using application/javascript as suggested by
    # http://www.ietf.org/rfc/rfc4329.txt
    return render_to_response('base/append_ourselves.js',
                              {'in_string': encoded_for_js},
                              mimetype='application/javascript')
