import urllib2
import logging
import mechanize
import lxml.etree

import mysite.customs.miro
import mysite.customs.ohloh
import mysite.customs.models
import mysite.search.models
import mysite.customs.bugtrackers.bugzilla_general

MOZILLA_GOOD_FIRST_BUG_QUERY='https://bugzilla.mozilla.org/buglist.cgi?resolution=---;status_whiteboard_type=substring;query_format=advanced;status_whiteboard=[good%20first%20bug]'
BUG_URL_PREFIX = 'https://bugzilla.mozilla.org/show_bug.cgi?id='

def get_current_bug_id2bug_objs():
    b = mysite.customs.ohloh.mechanize_get(MOZILLA_GOOD_FIRST_BUG_QUERY)

    # find the one form with ctype XML
    ctype_xml_form_no = mysite.customs.bugtrackers.bugzilla_general.find_ctype_xml_form_number(
        b.forms())

    # Click ze button
    b.select_form(nr=ctype_xml_form_no)
    b.submit()

    # Get a bunch of XML back
    bugzila_elt = lxml.etree.XML(b.response().read())

    ret = {}

    def project_finder_plugin(bug_elt):
        import mysite.search.models
        xml_project_name = bug_elt.xpath('product')[0].text

        ### Special-case the project names we know about
        mozilla2openhatch = {'Core': 'Mozilla Core',
                             'Firefox': 'Firefox',
                             'MailNews Core': 'Mozilla Messaging',
                             'addons.mozilla.org': 'addons.mozilla.org',
                             'Thunderbird': 'Thunderbird',
                             'Testing': 'Mozilla automated testing',
                             'Directory': 'Mozilla LDAP',
                             'mozilla.org': 'mozilla.org',
                             'SeaMonkey': 'SeaMonkey',
                             'Toolkit': 'Mozilla Toolkit',
                             'support.mozilla.com': 'support.mozilla.com',
                             'Camino': 'Camino',
                             'Calendar': 'Mozilla Calendar',
                             'Mozilla Localizations': 'Mozilla Localizations',
                             }
        if xml_project_name == 'Other Applications':
            project_name = 'Mozilla ' + bug_elt.xpath('component')[0].text
        else:
            project_name = mozilla2openhatch[xml_project_name]
        
        project, _ = mysite.search.models.Project.objects.get_or_create(
            name=project_name)
        return project

    for bug in bugzila_elt.xpath('bug'):
        bug_obj = mysite.customs.miro.bug_elt2bug_object(
            bug, canonical_bug_link_format_string=BUG_URL_PREFIX + '%d',
            gen_project=project_finder_plugin
            )
        bug_id = mysite.customs.bugtrackers.bugzilla_general.bug_url2bug_id(
            bug_obj.canonical_bug_link, BUG_URL_PREFIX=BUG_URL_PREFIX)
        bug_obj.good_for_newcomers = True
        bug_obj.bite_size_tag_name = '[good first bug]'
        ret[bug_id] = bug_obj
        
    return ret

def grab():
    """Loops over Mozilla's list of good first bugs and stores/updates
    them in our DB.
    
    For now, just grab the good first bugs to be kind to their servers."""

    current_bug_id2bug_objs = get_current_bug_id2bug_objs()

    bug_ids = mysite.customs.models.flatten(
        [current_bug_id2bug_objs.keys(),
         mysite.customs.bugtrackers.bugzilla_general.get_remote_bug_ids_already_stored(
             BUG_URL_PREFIX)])

    for bug_id in set(bug_ids):
        # Sometimes create_bug_object_for_remote_bug_id will fail to create
        # a bug because it's somehow gone missing. For those cases:

        # create canonical_bug_link in this function to avoid assuming the
        # returned bug is not None.
        canonical_bug_link = BUG_URL_PREFIX + str(bug_id)

        # If there is already a bug with this canonical_bug_link in
        # the DB, just delete it. Same story if the bug doens't 404!
        bugs_this_one_replaces = mysite.search.models.Bug.all_bugs.filter(
            canonical_bug_link=canonical_bug_link)
        for delete_me in bugs_this_one_replaces:
            delete_me.delete()

        if bug_id not in current_bug_id2bug_objs:
            continue # If the bug is not in the new data set, we're done here.

        bug = current_bug_id2bug_objs[bug_id]

        # Otherwise, print and save the sucker!
        print bug
        bug.save()
