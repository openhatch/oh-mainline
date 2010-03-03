# Imports {{{

# Python
import StringIO
import datetime
import urllib
import simplejson
import re
import collections

# Django
from django.template.loader import render_to_string
from django.core import serializers
from django.http import \
        HttpResponse, HttpResponseRedirect, HttpResponseServerError, HttpResponsePermanentRedirect
from django.shortcuts import \
        render_to_response, get_object_or_404
import django.contrib.auth 
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.core.cache import cache

# Haystack
import haystack.query

# OpenHatch apps
import mysite.base.controllers
import mysite.base.unicode_sanity
import mysite.profile.controllers
import mysite.base.helpers
from mysite.profile.models import \
        Person, Tag, TagType, \
        Link_Project_Tag, Link_Person_Tag, \
        DataImportAttempt, PortfolioEntry, Citation
from mysite.search.models import Project
from mysite.base.decorators import view
import mysite.profile.forms
import mysite.profile.tasks
# }}}

@login_required
def add_citation_manually_do(request):
    # {{{
    form = mysite.profile.forms.ManuallyAddACitationForm(request.POST)
    form.set_user(request.user)

    output = {
            'form_container_element_id': request.POST['form_container_element_id']
            }
    if form.is_valid():
        citation = form.save()

        # Manually added citations are published automatically.
        citation.is_published = True
        citation.save()
        
        json = simplejson.dumps(output)
        return HttpResponse(json, mimetype='application/json') 

    else:
        error_msgs = []
        for error in form.errors.values():
            error_msgs.extend(eval(error.__repr__())) # don't ask questions.

        output['error_msgs'] = error_msgs
        json = simplejson.dumps(output)
        return HttpResponseServerError(json, mimetype='application/json')

    #}}}

@view
def display_person_web(request, user_to_display__username=None):
    # {{{

    user = get_object_or_404(User, username=user_to_display__username)
    person, was_created = Person.objects.get_or_create(user=user)

    data = get_personal_data(person)
    data['edit_mode'] = False
    data['editable'] = (request.user == user)
    data['notifications'] = mysite.base.controllers.get_notification_from_request(request)
    data['explain_to_anonymous_users'] = True

    return (request, 'profile/main.html', data)

    # }}}

#FIXME: Create a separate function that just passes the data required for displaying the little user bar on the top right to the template, and leaves out all the data required for displaying the large user bar on the left.
def get_personal_data(person):
    # {{{

    # FIXME: Make this more readable.
    data_dict = {
            'person': person,
            'photo_url': person.get_photo_url_or_default(),
            } 

    data_dict['tags'] = tags_dict_for_person(person)
    data_dict['tags_flat'] = dict(
        [ (key, ', '.join([k.text for k in data_dict['tags'][key]]))
          for key in data_dict['tags'] ])

    data_dict['has_set_info'] = any(data_dict['tags_flat'].values())

    data_dict['contact_blurb'] = mysite.base.controllers.put_forwarder_in_contact_blurb_if_they_want(person.contact_blurb, person.user)

    return data_dict

    # }}}

def tags_dict_for_person(person):
    # {{{
    ret = collections.defaultdict(list)
    links = Link_Person_Tag.objects.filter(person=person).order_by('id')
    for link in links:
        ret[link.tag.tag_type.name].append(link.tag)

    return ret
    # }}}

# FIXME: Test this.
def widget_display_undecorated(request, user_to_display__username):
    """We leave this function unwrapped by @view """
    """so it can referenced by widget_display_string."""
    # {{{
    user = get_object_or_404(User, username=user_to_display__username)
    person = get_object_or_404(Person, user=user)

    data = get_personal_data(person)
    data.update(mysite.base.controllers.get_uri_metadata_for_generating_absolute_links(
        request))
    return (request, 'profile/widget.html', data)
    # }}}

widget_display = view(widget_display_undecorated)

def widget_display_string(request, user_to_display__username):
    request, template, data = widget_display_undecorated(request, user_to_display__username)
    return render_to_string(template, data)

def widget_display_js(request, user_to_display__username):
    # FIXME: In the future, use:
    html_doc = widget_display_string(request, user_to_display__username)
    # to generate html_doc
    encoded_for_js = simplejson.dumps(html_doc)
    # Note: using application/javascript as suggested by
    # http://www.ietf.org/rfc/rfc4329.txt
    return render_to_response('base/append_ourselves.js',
                              {'in_string': encoded_for_js},
                              mimetype='application/javascript')

# }}}

# Debtags {{{

def add_one_debtag_to_project(project_name, tag_text):
    # {{{
    tag_type, created = TagType.objects.get_or_create(name='Debtags')

    project, project_created = Project.objects.get_or_create(name=project_name)

    tag, tag_created = Tag.objects.get_or_create(
            text=tag_text, tag_type=tag_type)

    new_link = Link_Project_Tag.objects.create(
            tag=tag, project=project,
            source='Debtags')
    new_link.save()
    return new_link
# }}}

def list_debtags_of_project(project_name):
    # {{{
    debtags_list = list(TagType.objects.filter(name='Debtags'))
    if debtags_list:
        debtags = debtags_list[0]
    else:
        return []

    project_list = list(Project.objects.filter(name=project_name))
    if project_list:
        project = project_list[0]
    else:
        return []

    resluts = list(Link_Project_Tag.objects.filter(project=project,
        tag__tag_type=debtags))
    return [link.tag.text for link in resluts]
    # }}}

def import_debtags(cooked_string = None):
    # {{{
    if cooked_string is None:
        # Warning: this re-downloads the list from Alioth every time this
        # is called
        import urllib2
        import gzip
        fd = urllib2.urlopen('http://debtags.alioth.debian.org/tags/tags-current.gz')
        gzipped_sio = StringIO.StringIO(fd.read()) # this sucks, but I
        # can't stream to
        # gzip.GzipFile because
        # urlopen()'s result
        # lacks tell()
        gunzipped = gzip.GzipFile(fileobj=gzipped_sio)
    else:
        gunzipped = StringIO.StringIO(cooked_string)
    for line in gunzipped:
        if ':' in line:
            package, tagstring = line.split(':', 1)
            tags = map(lambda s: s.strip(), tagstring.split(','))
            for tag in tags:
                add_one_debtag_to_project(package, tag)
    # }}}

# }}}

# Project experience tags {{{

# }}}

def _project_hash(project_name):
    # {{{
    # This prefix is a sha256 of 1MiB of /dev/urandom
    PREFIX = '_project_hash_2136870e40a759b56b9ba97a0'
    PREFIX += 'd7f60b84dbc90097a32da284306e871105d96cd'
    import hashlib
    hashed = hashlib.sha256(PREFIX + project_name)
    return hashed.hexdigest()
    # }}}

@login_required
# this is a post handler
def edit_person_info(request):
    # {{{
    person = request.user.get_profile()

    #grab their submitted bio
    person.bio = request.POST.get('edit-tags-bio', '')

    # Grab the submitted homepage URL.
    # FIXME: One day, validate that this is a valid URL, and
    # use Django forms for this whole thing, while we're at it.
    person.homepage_url = request.POST.get('edit-tags-homepage_url', '')

    # We can map from some strings to some TagTypes
    for known_tag_type_name in ('understands', 'understands_not',
                           'studying', 'can_pitch_in', 'can_mentor'):
        tag_type, _ = TagType.objects.get_or_create(name=known_tag_type_name)

        text = request.POST.get('edit-tags-' + known_tag_type_name, '')
        # Set the tags to this thing
        new_tag_texts_for_this_type_raw = text.split(',')
        new_tag_texts_for_this_type = [tag.strip()
                for tag in new_tag_texts_for_this_type_raw]
        # Now figure out what tags are in the DB
        old_tag_links = Link_Person_Tag.objects.filter(
                tag__tag_type=tag_type, person=person)

        # FIXME: Churn, baby churn
        for link in old_tag_links:
            link.delete()

        for tag_text in new_tag_texts_for_this_type:
            if not tag_text.strip(): # Don't save blank tags.
                continue

            tag_text_case_sensitive_regex = r"^%s$" % re.escape(tag_text)
            tag, _ = Tag.objects.get_or_create(
                    text__regex=tag_text_case_sensitive_regex,
                    tag_type=tag_type,
                    defaults={'text': tag_text})
            new_link, _ = Link_Person_Tag.objects.get_or_create(
                    tag=tag, person=person)

    posted_contact_blurb = request.POST.get('edit-tags-contact_blurb', '')
    # if their new contact blurb contains $fwd,
    # make sure that they have an email address in our database
    # if not, give them an error
    if '$fwd' in posted_contact_blurb and not person.user.email:
        person.save()
        return edit_info(request, contact_blurb_error=True, contact_blurb_thus_far=posted_contact_blurb)

    person.contact_blurb = posted_contact_blurb
    person.save()

    # Enqueue a background task to re-index the person
    task = mysite.profile.tasks.ReindexPerson()
    task.delay(person_id=person.id)
    return HttpResponseRedirect(person.profile_url)

    # FIXME: This is racey. Only one of these functions should run at once.
    # }}}

@login_required
def ask_for_tag_input(request, username):
    # {{{
    return display_person_web(request, username, 'tags', edit='1')
    # }}}

def cut_list_of_people_in_three_columns(people):
    third = len(people)/3
    return [people[0:third], people[third:(third*2)], people[(third*2):]]

def cut_list_of_people_in_two_columns(people):
    half = len(people)/2
    return [people[0:half], people[half:]]
    
def permanent_redirect_to_people_search(request, property, value):
    '''Property is the "tag name", and "value" is the text in it.'''
    if property == 'seeking':
        property = 'can_pitch_in'
    
    if ' ' in value:
        escaped_value = '"' + value + '"'
    else:
        escaped_value = value
    
    q = '%s:%s' % (property, escaped_value)
    get_args = {u'q': q}
    destination_url = (reverse('mysite.profile.views.people') + '?' + 
                       mysite.base.unicode_sanity.urlencode(get_args))
    return HttpResponsePermanentRedirect(destination_url)

def tag_type_query2mappable_orm_people(tag_type_short_name, parsed_query):
    # ask haystack...
    tag_type_according_to_haystack = tag_type_short_name + "_lowercase_exact"
    mappable_people_from_haystack = haystack.query.SearchQuerySet().all()
    mappable_people_from_haystack = mappable_people_from_haystack.filter(**{
            tag_type_according_to_haystack: parsed_query['q'].lower()})

    mappable_people_from_haystack.load_all()

    mappable_people = [x.object for x in mappable_people_from_haystack if x.object]

    ### and sort it the way everyone expects
    mappable_people = sorted(mappable_people, key=lambda p: p.user.username.lower())

    return mappable_people, {}

def all_tags_query2mappable_orm_people(parsed_query):
    # do three queries...
    # the values are set()s containing ID numbers of Django ORM Person objects
    queries_in_order = ['can_mentor_lowercase_exact',
                        'can_pitch_in_lowercase_exact',
                        'understands_lowercase_exact']
    query2results = {queries_in_order[0]: set(),
                     queries_in_order[1]: set(),
                     queries_in_order[2]: set()}
    for query in query2results:
        # ask haystack...
        mappable_people_from_haystack = haystack.query.SearchQuerySet().all()
        mappable_people_from_haystack = mappable_people_from_haystack.filter(**{query: parsed_query['q'].lower()})
        
        mappable_people_from_haystack.load_all()
                
        results = [x.object for x in mappable_people_from_haystack]
        query2results[query] = results

        ### mappable_people
        mappable_people_set = set()
        for result_set in query2results.values():
            mappable_people_set.update(result_set)

        ### and sort it the way everyone expects
        mappable_people = sorted(mappable_people_set, key=lambda p: p.user.username.lower())

        ### Justify your existence time: Why is each person a valid match?
        for person in mappable_people:
            person.reasons = [query for query in queries_in_order
                              if person in query2results[query]]

            # now we have to clean this up. First, remove teh _lowercase_exact from the end
            person.reasons = [ s.replace('_lowercase_exact', '') for s in person.reasons]
            # then make it the human readable form as said by the TagType dict
            person.reasons = [TagType.short_name2long_name[s] for s in person.reasons]

    extra_data = {}
    ## How many possible mentors
    extra_data['suggestions_for_searches_regarding_people_who_can_mentor'] = []
    mentor_people = query2results['can_mentor_lowercase_exact']
    if mentor_people:
        extra_data['suggestions_for_searches_regarding_people_who_can_mentor'].append(
            {'query': parsed_query['q'].lower(),
             'count': len(mentor_people)})

    extra_data['suggestions_for_searches_regarding_people_who_can_pitch_in'] = []
    ## Does this relate to people who can pitch in?
    can_pitch_in_people = query2results['can_pitch_in_lowercase_exact']
    if can_pitch_in_people:
        extra_data['suggestions_for_searches_regarding_people_who_can_pitch_in'].append(
            {'query': parsed_query['q'].lower(), 'count': len(can_pitch_in_people)})

    return mappable_people, extra_data

def query2results(parsed_query):
    query_type2executor = {
        'project': project_query2mappable_orm_people,
        'all_tags': all_tags_query2mappable_orm_people}
    
    # Now add to that the TagType-based queries
    for short_name in mysite.profile.models.TagType.short_name2long_name:
        def thingamabob(parsed_query, short_name=short_name):
            return tag_type_query2mappable_orm_people(short_name, parsed_query)
        query_type2executor[short_name] = thingamabob

    desired_query_type = parsed_query['query_type']
    return query_type2executor[desired_query_type](parsed_query)

def project_query2mappable_orm_people(parsed_query):
    assert parsed_query['query_type'] == 'project'
    mappable_people_from_haystack = haystack.query.SearchQuerySet().all()
    haystack_field_name = 'all_public_projects_lowercase_exact'
    mappable_people_from_haystack = mappable_people_from_haystack.filter(
        **{haystack_field_name: parsed_query['q'].lower()})
    
    mappable_people_from_haystack.load_all()
    
    mappable_people = sorted([x.object for x in mappable_people_from_haystack],
                             key=lambda x: x.user.username)

    extra_data = {}

    ## populate suggestions_for_searches_regarding_people_who_can_pitch_in
    ## that expects a {'query': X, 'count': Y} dict
    suggestions_for_searches_regarding_people_who_can_pitch_in = []
    orm_projects = Project.objects.filter(name__iexact=parsed_query['q'])
    for orm_project in orm_projects:
        people_who_can_pitch_in_with_project_language = haystack.query.SearchQuerySet(
            ).all().filter(can_pitch_in_lowercase_exact=orm_project.language.lower())
        if people_who_can_pitch_in_with_project_language:
            suggestions_for_searches_regarding_people_who_can_pitch_in.append(
                {'query': orm_project.language,
                 'count': len(people_who_can_pitch_in_with_project_language),
                 'summary_addendum': ", %s's primary language" % orm_project.name})


    # Suggestions for possible mentors
    suggestions_for_searches_regarding_people_who_can_mentor = []
    for orm_project in orm_projects:
        people_who_could_mentor_in_the_project_language = haystack.query.SearchQuerySet(
            ).all().filter(can_mentor_lowercase_exact=orm_project.language.lower())
        if people_who_could_mentor_in_the_project_language:
            suggestions_for_searches_regarding_people_who_can_mentor.append(
                {'query': orm_project.language,
                 'count': len(people_who_could_mentor_in_the_project_language),
                 'summary_addendum': ", %s's primary language" % orm_project.name})

    extra_data['suggestions_for_searches_regarding_people_who_can_pitch_in'
               ] = suggestions_for_searches_regarding_people_who_can_pitch_in

    extra_data['suggestions_for_searches_regarding_people_who_can_mentor'
               ] = suggestions_for_searches_regarding_people_who_can_mentor
    
    return mappable_people, extra_data

@view
def people(request):
    """Display a list of people."""
    # {{{
    data = {}

    # pull in q from GET
    query = request.GET.get('q', '')

    data['raw_query'] = query
    parsed_query = mysite.profile.controllers.parse_string_query(query)
    data.update(parsed_query)

    if parsed_query['query_type'] != 'project':
        # Figure out which projects happen to match that
        projects_that_match_q_exactly = []
        for word in [parsed_query['q']]: # This is now tokenized smartly.
            name_matches = Project.objects.filter(name__iexact=word)
            for project in name_matches:
                if project.cached_contributor_count:
                    # only add those projects that have people in them
                    projects_that_match_q_exactly.append(project)
        data['projects_that_match_q_exactly'] = projects_that_match_q_exactly

    # Get the list of people to display.

    if parsed_query['q'].strip():
        everybody, extra_data = query2results(parsed_query)
        data.update(extra_data)

    else:
        everybody = Person.objects.all().order_by('user__username')

    # filter by query, if it is set
    data['people'] = everybody
    get_relevant_person_data = lambda p: (
            {'name': p.get_full_name_or_username(),
            'location': p.get_public_location_or_default()})
    person_id2data = dict([(person.pk, get_relevant_person_data(person))
            for person in everybody])
    data['person_id2data_as_json'] = simplejson.dumps(person_id2data)
    data['test_js'] = request.GET.get('test', None)
    data['num_of_persons_with_locations'] = len(person_id2data)
    if request.GET.get('center', False):
        data['center_json'] = mysite.base.controllers.cached_geocoding_in_json(
            request.GET.get('center', ''))
        # the below is true when we fail to geocode the center that we got from GET
        if data['center_json'] == 'null':
            data['geocode_failed'] = True;
        data['center_name'] = request.GET.get('center', '')
        data['center_name_json'] = simplejson.dumps(request.GET.get('center', ''))

    data['show_everybody_javascript_boolean'] = simplejson.dumps(not data.get('center_json', False))

    data['person_id2lat_long_as_json'] = simplejson.dumps(
        dict( (person_id, simplejson.loads(mysite.base.controllers.cached_geocoding_in_json(person_id2data[person_id]['location'])))
              for person_id in person_id2data))

    suggestion_count = 6

    cache_timespan = 86400 * 7
    #if settings.DEBUG:
    #    cache_timespan = 0

    key_name = 'most_popular_projects'
    popular_projects = cache.get(key_name)
    if popular_projects is None:
        projects = Project.objects.all()
        popular_projects = sorted(projects, key=lambda proj: len(proj.get_contributors())*(-1))[:suggestion_count]
        #extract just the names from the projects
        popular_projects = [project.name for project in popular_projects]
        # cache it for a week
        cache.set(key_name, popular_projects, cache_timespan)

    key_name = 'most_popular_tags'
    popular_tags = cache.get(key_name)
    if popular_tags is None:
        # to get the most popular tags:
            # get all tags
            # order them by the number of people that list them
            # remove duplicates
        tags = Tag.objects.all()
        #lowercase them all and then remove duplicates
        tags_with_no_duplicates = list(set(map(lambda tag: tag.name.lower(), tags)))
        #take the popular ones
        popular_tags = sorted(tags_with_no_duplicates, key=lambda tag_name: len(Tag.get_people_by_tag_name(tag_name))*(-1))[:suggestion_count]
        # cache it for a week
        cache.set(key_name, popular_tags, cache_timespan)

    # Populate matching_project_suggestions
    data['matching_project_suggestions'] = Project.objects.filter(
        cached_contributor_count__gt=0, name__icontains=data['q']).filter(
        ~Q(name__iexact=data['q'])).order_by(
        '-cached_contributor_count')

    MATCHING_PROJECT_SUGGESTIONS_COUNT = 3
    # limit this if we found people
    if data['people']:
        data['matching_project_suggestions'] = data['matching_project_suggestions'][:MATCHING_PROJECT_SUGGESTIONS_COUNT]

    # What kind of people are these?
    if data['q']:
        if data['query_type'] == 'project':
            data['this_query_summary'] = 'who have contributed to'
        elif data['query_type'] == 'all_tags':
            data['this_query_summary'] = 'who have listed'
            data['this_query_post_summary'] = ' on their profiles'
        elif data['query_type'] == 'understands_not':
            data['this_query_summary'] = 'tagged with understands_not = '
        elif data['query_type'] == 'understands':
            data['this_query_summary'] = 'who understand '
        elif data['query_type'] == 'studying':
            data['this_query_summary'] = 'who are currently studying '
        else:
            long_name = mysite.profile.models.TagType.short_name2long_name[data['query_type']]
            data['this_query_summary'] = 'who ' + long_name

    data['suggestions'] = [
        dict(display_name='projects',
             values=popular_projects,
             query_prefix='project:'),
        dict(display_name='profile tags',
             values=popular_tags,
             query_prefix='')]

    return (request, 'profile/search_people.html', data)
    # }}}

def gimme_json_for_portfolio(request):
    "Get JSON used to live-update the portfolio editor."
    """JSON includes:
        * The person's data.
        * DataImportAttempts.
        * other stuff"""
    # {{{
    person = request.user.get_profile()

    # Citations don't naturally serialize summaries.
    citations = list(Citation.untrashed.filter(portfolio_entry__person=person))
    portfolio_entries_unserialized = PortfolioEntry.objects.filter(person=person, is_deleted=False).order_by('-pk')
    projects_unserialized = [p.project for p in portfolio_entries_unserialized]
    
    # Serialize citation summaries
    summaries = {}
    for c in citations:
        summaries[c.pk] = render_to_string(
                "profile/portfolio/citation_summary.html",
                {'citation': c})

    # FIXME: Maybe we can serialize directly to Python objects.
    # fixme: zomg       don't recycle variable names for objs of diff types srsly u guys!

    five_minutes_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
    recent_dias = DataImportAttempt.objects.filter(person=person, date_created__gt=five_minutes_ago)
    recent_dias_json = simplejson.loads(serializers.serialize('json', recent_dias))
    portfolio_entries = simplejson.loads(serializers.serialize('json',
        portfolio_entries_unserialized))
    projects = simplejson.loads(serializers.serialize('json', projects_unserialized))
    # FIXME: Don't send like all the flippin projects down the tubes.
    citations = simplejson.loads(serializers.serialize('json', citations))

    recent_dias_that_are_completed = recent_dias.filter(completed=True)
    import_running = recent_dias.count() > 0 and (
            recent_dias_that_are_completed.count() != recent_dias.count())
    progress_percentage = 100
    if import_running:
        progress_percentage = int(recent_dias_that_are_completed.count() * 100.0 / recent_dias.count())
    import_data = {
            'running': import_running,
            'progress_percentage': progress_percentage,
            }

    json = simplejson.dumps({
        'dias': recent_dias_json,
        'import': import_data,
        'citations': citations,
        'portfolio_entries': portfolio_entries,
        'projects': projects,
        'summaries': summaries,
        'messages': request.user.get_and_delete_messages(),
        })

    return HttpResponse(json, mimetype='application/json')
    # }}}

def replace_icon_with_default(request):
    "Expected postcondition: project's icon_dict says it is generic."
    """
    Expected output will look something like this:
    {
            'success': true,
            'portfolio_entry__pk': 0
    }"""
    portfolio_entry = PortfolioEntry.objects.get(
            pk=int(request.POST['portfolio_entry__pk']),
            person__user=request.user)
    # FIXME: test for naughty people trying to replace others' icons with the default!
    project = portfolio_entry.project

    # set as default
    project.icon_is_wrong = True
    project.save()

    # TODO: email all@ letting them know that we did so
    mysite.profile.tasks.send_email_to_all_because_project_icon_was_marked_as_wrong.delay(project.pk, project.name, project.icon_for_profile.url)


    # prepare output
    data = {}
    data['success'] = True
    data['portfolio_entry__pk'] = portfolio_entry.pk
    return mysite.base.helpers.json_response(data)

@login_required
def prepare_data_import_attempts_do(request):
    """
    Input: request.POST contains a list of usernames or email addresses.
    These are identifiers under which the authorized user has committed code
    to an open-source repository, or at least so says the user.
    
    Side-effects: Create DataImportAttempts that a user might want to execute.

    Not yet implemented: This means, don't show the user DIAs that relate to
    non-existent accounts on remote networks. And what *that* means is, 
    before bothering the user, ask those networks beforehand if they even 
    have accounts named identifiers[0], etc."""
    # {{{

    # For each commit identifier, prepare some DataImportAttempts.
    prepare_data_import_attempts(identifiers=request.POST.values(), user=request.user)

    return HttpResponse('1')
    # }}}

def prepare_data_import_attempts(identifiers, user):
    "Enqueue and track importation tasks."
    """Expected input: A list of committer identifiers, e.g.:
    ['paulproteus', 'asheesh@asheesh.org']

    For each data source, enqueue a background task.
    Keep track of information about the task in an object
    called a DataImportAttempt."""

    # Side-effects: Create DIAs that a user might want to execute.
    for identifier in identifiers:
        if identifier.strip(): # Skip blanks or whitespace
            for source_key, _ in DataImportAttempt.SOURCE_CHOICES:
                dia = DataImportAttempt(
                        query=identifier,
                        source=source_key,
                        person=user.get_profile())
                dia.save()
                dia.do_what_it_says_on_the_tin()

@login_required
@view
def importer(request, test_js = False):
    """Get the DIAs for the logged-in user's profile. Pass them to the template."""
    # {{{

    blank_query_index = 0
    checkboxes = []
    for source_key, source_display in DataImportAttempt.SOURCE_CHOICES:
        checkboxes.append({
            'id': "%s%d" % (source_key, blank_query_index),
            'label': source_display,
            })
    blank_query = {
            'index': blank_query_index,
            'checkboxes': checkboxes
            }
    person = request.user.get_profile()
    data = get_personal_data(person)
    data['dias'] = DataImportAttempt.objects.filter(person=person).order_by('id')
    data['blank_query'] = blank_query

    # This is used to create a blank 'Add another record' form, which is printed
    # to the bottom of the importer page. The HTML underlying this form is used
    # to generate forms dynamically.
    data['citation_form'] = mysite.profile.forms.ManuallyAddACitationForm(auto_id=False)

    # This variable is checked in base/templates/base/base.html
    data['test_js'] = test_js

    return (request, 'profile/importer.html', data)
    # }}}

#FIXME: Rename importer
portfolio_editor = importer

def portfolio_editor_test(request):
    return portfolio_editor(request, test_js=True)

def filter_by_key_prefix(dict, prefix):
    """Return those and only those items in a dictionary whose keys have the given prefix."""
    out_dict = {}
    for key, value in dict.items():
        if key.startswith(prefix):
            out_dict[key] = value
    return out_dict

@login_required
def user_selected_these_dia_checkboxes(request):
    """ Input: Request POST contains a list of checkbox IDs corresponding to DIAs.
    Side-effect: Make a note on the DIA that its affiliated person wants it.
    Output: Success?
    """
    # {{{

    prepare_data_import_attempts(request.POST, request.user)

    checkboxes = filter_by_key_prefix(request.POST, "person_wants_")
    identifiers = filter_by_key_prefix(request.POST, "identifier_")

    for checkbox_id, value in checkboxes.items():
        if value == 'on':
            x, y, identifier_index, source_key = checkbox_id.split('_')
            identifier = identifiers["identifier_%s" % identifier_index]
            if identifier:
                # FIXME: For security, ought this filter include only dias
                # associated with the logged-in user's profile?
                dia = DataImportAttempt(
                        identifier, source_key,
                        request.user.get_profile())
                dia.person_wants_data = True
                dia.save()
                dia.do_what_it_says_on_the_tin()

                # There may be data waiting or not,
                # but no matter; this function may
                # run unconditionally.
                dia.give_data_to_person()

    return HttpResponse('1')
    # }}}

@login_required
@view
def display_person_edit_name(request, name_edit_mode):
    '''Show a little edit form for first name and last name.

    Why separately handle first and last names? The Django user
    model already stores them separately.
    '''
    # {{{
    data = get_personal_data(request.user.get_profile())
    data['name_edit_mode'] = name_edit_mode
    data['editable'] = True
    return (request, 'profile/main.html', data)
    # }}}


@login_required
def display_person_edit_name_do(request):
    '''Take the new first name and last name out of the POST.

    Jam them into the Django user model.'''
    # {{{
    user = request.user

    new_first = request.POST['first_name']
    new_last = request.POST['last_name']

    user.first_name = new_first
    user.last_name = new_last
    user.save()

    return HttpResponseRedirect('/people/%s' % urllib.quote(user.username))
    # }}}

@login_required
def publish_citation_do(request):
    try:
        pk = request.POST['pk']
    except KeyError:
        return HttpResponse("0")

    try:
        c = Citation.objects.get(pk=pk, portfolio_entry__person__user=request.user)
    except Citation.DoesNotExist:
        return HttpResponse("0")

    c.is_published = True
    c.save()

    return HttpResponse("1")

@login_required
def delete_citation_do(request):
    try:
        pk = request.POST['citation__pk']
    except KeyError:
        return HttpResponse("0")

    try:
        c = Citation.objects.get(pk=pk, portfolio_entry__person__user=request.user)
    except Citation.DoesNotExist:
        return HttpResponse("0")

    c.is_deleted = True
    c.save()

    return HttpResponse("1")

@login_required
def delete_portfolio_entry_do(request):
    try:
        pk = int(request.POST['portfolio_entry__pk'])
    except KeyError:
        return mysite.base.helpers.json_response({'success': False})

    try:
        p = PortfolioEntry.objects.get(pk=pk, person__user=request.user)
    except PortfolioEntry.DoesNotExist:
        return mysite.base.helpers.json_response({'success': False})

    p.is_deleted = True
    p.save()

    return mysite.base.helpers.json_response({
            'success': True,
            'portfolio_entry__pk': pk})
         

@login_required
def save_portfolio_entry_do(request):
    pk = request.POST['portfolio_entry__pk']

    if pk == 'undefined':
        project, _ = Project.objects.get_or_create(name=request.POST['project_name'])
        p = PortfolioEntry(project=project, person=request.user.get_profile())
    else:
        p = PortfolioEntry.objects.get(pk=pk, person__user=request.user)
    p.project_description = request.POST['project_description']
    p.experience_description = request.POST['experience_description']
    p.is_published = True
    p.save()

    # Publish all attached Citations
    citations = Citation.objects.filter(portfolio_entry=p)
    for c in citations:
        c.is_published = True
        c.save()

    return mysite.base.helpers.json_response({
            'success': True,
            'pf_entry_element_id': request.POST['pf_entry_element_id'],
            'portfolio_entry__pk': p.pk
        })

@login_required
def dollar_username(request):
    return HttpResponseRedirect(reverse(display_person_web,
		kwargs={'user_to_display__username': 
                request.user.username}))

@login_required
@view
def edit_info(request, contact_blurb_error=False, contact_blurb_thus_far=''):
    person = request.user.get_profile()
    data = get_personal_data(person)
    data['info_edit_mode'] = True
    data['contact_blurb_error'] = contact_blurb_error
    if contact_blurb_error:
        data['contact_blurb'] = contact_blurb_thus_far
    else:
        data['contact_blurb'] = person.contact_blurb
    return request, 'profile/info_wrapper.html', data

# vim: ai ts=3 sts=4 et sw=4 nu
