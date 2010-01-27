# -*- coding: utf-8 -*-

from django.http import HttpResponse, \
        HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response
from django_authopenid.forms import OpenidSigninForm
import simplejson
from django.template import RequestContext, loader, Context
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import AuthenticationForm

import mysite.profile as profile
import mysite.account
import mysite.profile.controllers
import mysite.account.forms
from mysite.profile.views import display_person_web
from mysite.base.decorators import view
import mysite.customs.feed
import mysite.search.controllers

import feedparser
import lxml.html
import random

from django.contrib.auth.decorators import login_required

def homepage(request, signup_form=None,
        invitation_request_form=None, initial_tab_open='login'):

    #if request.user.is_authenticated():
    return landing_page(request)

    openid_signin_form = OpenidSigninForm()

    old_fashioned_authentication_form = AuthenticationForm()

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
            'old_fashioned_authentication_form': old_fashioned_authentication_form,
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

@view
def landing_page(request):

    data = {}
    data['entries'] = mysite.customs.feed.cached_blog_entries()[:3]

    recommended_bugs = []
    if request.user.is_authenticated():
        suggested_searches = request.user.get_profile().get_recommended_search_terms()
        recommended_bugs = mysite.profile.controllers.recommend_bugs(suggested_searches, n=5)

    data['recommended_bugs'] = list(recommended_bugs) # A list so we can tell if it's empty

    everybody = list(mysite.profile.models.Person.objects.exclude(photo=''))
    random.shuffle(everybody)
    data['random_profiles'] = everybody[0:5]


    data['nudge_projects'] = True # This value might be overwritten below.
    
    #get globally recommended bug search stuff (for anonymous users)
    if request.user.is_authenticated():
        # for logged-in users:
        # figure oout which nudges we want to show them
        person = request.user.get_profile()

        data['nudge_location'] = not person.location_display_name or not person.location_confirmed
        data['nudge_projects'] = not person.dataimportattempt_set.all()
        data['nudge_tags'] = not person.get_tags_for_recommendations()

        data['show_nudge_box'] = (data['nudge_location'] or 
                data['nudge_projects'] or data['nudge_tags'])
    if not data['recommended_bugs']:
        data['show_nudge_box'] = True
        # a dict pairing two things:
        # * GET data dicts (to be passed to Query's create_from_GET_data)
        # * strings of HTML representing the bug classification
        recommended_bug_string2GET_data_dicts = {
        "<strong>Bitesize</strong> bugs whose main project language is <strong>C</strong>":
            {'language':'C', 'toughness':'bitesize'},
        "<strong>Bitesize</strong> bugs matching &lsquo;<strong>audio</strong>&rsquo;":
            {'q':'audio', 'toughness':'bitesize'},
        "Bugs matching <strong>unicode</strong>":
            {'q':'unicode'},
        "Requests for <strong>documentation writing/editing</strong>":
            {'contribution_type':'documentation'},
        #"Requests for <strong>documentation writing/editing</strong>":
        #    {'contribution_type':'documentation'},
        }
        recommended_bug_string2Query_objects = {}
        for (string, GET_data_dict) in recommended_bug_string2GET_data_dicts.items():
            query = mysite.search.controllers.Query.create_from_GET_data(GET_data_dict)
            recommended_bug_string2Query_objects[string] = query

        data['recommended_bug_string2Query_objects'] = recommended_bug_string2Query_objects

    return (request, 'base/landing.html', data)

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

def page_not_found(request):
    return render_to_response('404.html', {'the_user': request.user })
