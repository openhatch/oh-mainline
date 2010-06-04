# -*- coding: utf-8 -*-

from django.http import HttpResponse, \
        HttpResponseRedirect, HttpResponseServerError, HttpResponseBadRequest
from mysite.base.helpers import render_response
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
import mysite.search.models

import feedparser
import lxml.html
import random
import datetime

from django.contrib.auth.decorators import login_required

def front_page_data():
    data = {}
    data['entries'] = mysite.customs.feed.cached_blog_entries()[:1]
    feed_items = list(mysite.search.models.Answer.objects.order_by('-modified_date')[:5])
    feed_items.extend(mysite.search.models.WannaHelperNote.objects.order_by('-modified_date')[:5])
    feed_items.sort(key=lambda x: x.modified_date, reverse=True)
    data['recent_feed_items'] = feed_items[:5]
    return data

@view
def home(request):
    data = front_page_data()

    recommended_bugs = []
    if request.user.is_authenticated():
        suggested_searches = request.user.get_profile().get_recommended_search_terms()
        recommender = mysite.profile.controllers.RecommendBugs(
            suggested_searches, n=5)
        recommended_bugs = recommender.recommend()

    data['recommended_bugs'] = list(recommended_bugs) # A list so we can tell if it's empty

    everybody = list(mysite.profile.models.Person.objects.exclude(link_person_tag=None))
    random.shuffle(everybody)
    data['random_profiles'] = everybody[0:5]

    #get globally recommended bug search stuff (for anonymous users)
    if request.user.is_authenticated():
        # for logged-in users:
        # figure oout which nudges we want to show them
        person = request.user.get_profile()

        data['nudge_location'] = person.should_be_nudged_about_location()
        data['nudge_tags'] = not person.get_tags_for_recommendations()

        # Project editor nudging. Note:
        # If the person has some dias, then no nudge!
        if person.dataimportattempt_set.all():
            pass # whee, no nudge. the user has already seen the project editor.
        else:
            # So, either the person has some projects listed publicly, in which case,
            # we should remind the person just to use the importer...
            if person.get_published_portfolio_entries():
                data['nudge_importer_when_user_has_some_projects'
                     ] = True # just nudge about the importer...
            else:
                # the person has entered zero projects and hasn't touched the importer
                # so introduce him or her to use the importer!
                data['nudge_importer_when_user_has_no_projects'
                     ] = True # give the general project editing nudge

        data['show_nudge_box'] = (data['nudge_location'] or 
                'nudge_importer_when_user_has_no_projects' in data or data['nudge_tags'] or
                                  'nudge_importer_when_user_has_some_projects' in data)
    else: # no user logged in. Show front-page importer nudge.
        data['nudge_importer_when_user_has_no_projects'] = True

    if not data['recommended_bugs']:
        data['show_nudge_box'] = True
        # a dict pairing two things:
        # * GET data dicts (to be passed to Query's create_from_GET_data)
        # * strings of HTML representing the bug classification
        recommended_bug_string2GET_data_dicts = {
        "<strong>Bitesize</strong> bugs whose main project language is <strong>C</strong>":
            {u'language':u'C', u'toughness':u'bitesize'},
        "<strong>Bitesize</strong> bugs matching &lsquo;<strong>audio</strong>&rsquo;":
            {u'q':u'audio', u'toughness':u'bitesize'},
        "Bugs matching &lsquo;<strong>unicode</strong>&rsquo;":
            {u'q':u'unicode'},
        "Requests for <strong>documentation writing/editing</strong>":
            {u'contribution_type':u'documentation'},
        #"Requests for <strong>documentation writing/editing</strong>":
        #    {u'contribution_type':u'documentation'},
        }
        recommended_bug_string2Query_objects = {}
        for (string, GET_data_dict) in recommended_bug_string2GET_data_dicts.items():
            query = mysite.search.controllers.Query.create_from_GET_data(GET_data_dict)
            recommended_bug_string2Query_objects[string] = query

        data[u'recommended_bug_string2Query_objects'] = recommended_bug_string2Query_objects

    if request.user.is_authenticated():
        return (request, 'base/landing_page_for_logged_in_users.html', data)
    else:
        return (request, 'base/landing.html', data)

def page_to_js(request):
    # FIXME: In the future, use:
    # from django.template.loader import render_to_string
    # to generate html_doc
    html_doc = "<strong>zomg</strong>"
    encoded_for_js = simplejson.dumps(html_doc)
    # Note: using application/javascript as suggested by
    # http://www.ietf.org/rfc/rfc4329.txt
    return render_response(request, 'base/append_ourselves.js',
                              {'in_string': encoded_for_js},
                              mimetype='application/javascript')

def page_not_found(request):
    t = loader.get_template('404.html')
    c = Context({
        'the_user': request.user
    })

    response = HttpResponse(t.render(c), status=404)
    return response



def geocode(request):
    address = request.GET.get('address', None)
    if not address:
        return HttpResponseBadRequest() # no address :-(
    # try to geocode
    coordinates_as_json = mysite.base.controllers.cached_geocoding_in_json(address)
    if coordinates_as_json == 'null':
        # We couldn't geocode that.
        return HttpResponseBadRequest() # no address :-(
    return HttpResponse(coordinates_as_json, 
                        mimetype='application/json')

@view
def meta(request):
    data = {}
    data['dia_diagnostics'] = {}

    # temp variable for shortness
    my = data['dia_diagnostics']
    
    my['Uncompleted DIAs'] = mysite.profile.models.DataImportAttempt.objects.filter(
        completed=False).count()

    one_minute_ago = (datetime.datetime.now() -
                      datetime.timedelta(minutes=1))

    my['Uncompleted DIAs older than 1 minute'] = mysite.profile.models.DataImportAttempt.objects.filter(
        completed=False, date_created__lt=one_minute_ago).count()

    five_minute_ago = (datetime.datetime.now() -
                      datetime.timedelta(minutes=5))

    my['Uncompleted DIAs older than 5 minutes'] = mysite.profile.models.DataImportAttempt.objects.filter(
        completed=False, date_created__lt=one_minute_ago).count()
        
    data['bug_diagnostics'] = {}
    # local name for shortness
    my = data['bug_diagnostics']

    one_hour_and_one_day_ago = (datetime.datetime.now() -
                                datetime.timedelta(days=1, hours=1))

    my['Bugs last polled more than than one day + one hour ago'] = mysite.search.models.Bug.all_bugs.filter(
        last_polled__lt=one_hour_and_one_day_ago).count()

    two_days_ago = (datetime.datetime.now() -
                    datetime.timedelta(days=2))
    my['Bugs last polled more than two days ago'] = mysite.search.models.Bug.all_bugs.filter(
        last_polled__lt=two_days_ago).count()
    my['Bugs last polled more than two days ago (in percent)'] = (
        mysite.search.models.Bug.all_bugs.filter(
        last_polled__lt=two_days_ago).count() * 100.0 /
        mysite.search.models.Bug.all_bugs.count())        

    return (request, 'meta.html', data)

@login_required
def save_portfolio_entry_ordering_do(request):
    from mysite.profile.models import PortfolioEntry

    list_of_ids = request.POST.getlist('sortable_portfolio_entry[]')
    are_we_archiving_yet = False
    for n, id in enumerate(list_of_ids):
        if id == 'FOLD': # ha not an id
            are_we_archiving_yet = True
            continue
        pfe = PortfolioEntry.objects.get(id=int(id), person__user=request.user)
        pfe.sort_order = n
        pfe.is_archived = are_we_archiving_yet
        pfe.save()
    return HttpResponse('1')

@view
def landing_for_opp_hunters(request):
    return (request, 'landing_for_opp_hunters.html',
            front_page_data())

@view
def landing_for_project_maintainers(request):
    return (request, 'landing_for_project_maintainers.html',
            front_page_data())

@view
def landing_for_documenters(request):
    return (request, 'landing_for_documenters.html',
            front_page_data())

@view
def test_weekly_email_re_projects(request):
    from mysite.profile.management.commands import send_weekly_emails
    from mysite.profile.models import Person
    command = send_weekly_emails.Command()
    command.this_run_covers_things_since = datetime.datetime(2009, 5, 28)
    command.this_run_covers_things_up_until = datetime.datetime.utcnow()
    context = command.get_context_for_weekly_email_to(Person.get_by_username('paulproteus'))
    return (request, 'weekly_email_re_projects.txt', context)
