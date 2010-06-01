import urllib2
import logging
import mechanize
import lxml.etree

import mysite.customs.miro
import mysite.customs.ohloh
import mysite.customs.models
import mysite.search.models

from itertools import chain

def bug_url2bug_id(url, BUG_URL_PREFIX):
    before, after = url.split(BUG_URL_PREFIX)
    return int(after)

def bug_id2bug_url(bug_id, BUG_URL_PREFIX):
    return BUG_URL_PREFIX + str(bug_id)

def get_remote_bug_ids_already_stored(BUG_URL_PREFIX):
    for bug in mysite.search.models.Bug.all_bugs.filter(
        canonical_bug_link__contains=BUG_URL_PREFIX):
        yield bug_url2bug_id(
            bug.canonical_bug_link, BUG_URL_PREFIX=BUG_URL_PREFIX)

def find_ctype_xml_form_number(forms):
    for n, form in enumerate(forms):
        try:
            value = form.get_value('ctype')
            if value == 'xml':
                return n
        except:
            pass
    raise ValueError, "Could not find the right form."

def query_url2bug_objects(BUG_URL_PREFIX,
                          QUERY_URL,
                          project_finder_plugin,
                          detect_if_good_for_newcomers_plugin):
    b = mysite.customs.ohloh.mechanize_get(QUERY_URL)

    # find the one form with ctype XML
    ctype_xml_form_no = find_ctype_xml_form_number(b.forms())

    # Click ze button
    b.select_form(nr=ctype_xml_form_no)
    b.submit()

    # Get a bunch of XML back
    bugzila_elt = lxml.etree.XML(b.response().read())

    ret = {}

    for bug in bugzila_elt.xpath('bug'):
        bug_obj = mysite.customs.miro.bug_elt2bug_object(
            bug, canonical_bug_link_format_string=BUG_URL_PREFIX + '%d',
            gen_project=project_finder_plugin
            )
        bug_id = mysite.customs.bugtrackers.bugzilla_general.bug_url2bug_id(
            bug_obj.canonical_bug_link, BUG_URL_PREFIX=BUG_URL_PREFIX)
        detect_if_good_for_newcomers_plugin(bug, bug_obj)
        ret[bug_id] = bug_obj
        
    return ret

def grab(current_bug_id2bug_objs,
         BUG_URL_PREFIX):
    bug_ids = chain(
        current_bug_id2bug_objs.keys(),
        get_remote_bug_ids_already_stored(BUG_URL_PREFIX))

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
        logging.info("Got a bug: %s" % bug)
        bug.save()
