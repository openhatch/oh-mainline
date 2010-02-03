import urllib2
import mysite.customs.miro
import mechanize
import mysite.customs.ohloh
import lxml.etree
import mysite.customs.models
import mysite.search.models

GNOME_LOVE_QUERY='https://bugzilla.gnome.org/buglist.cgi?columnlist=id&keywords=gnome-love&query_format=advanced&resolution=---'
BUG_URL_PREFIX = 'https://bugzilla.gnome.org/show_bug.cgi?id='

def find_ctype_xml_form_number(forms):
    for n, form in enumerate(forms):
        try:
            value = form.get_value('ctype')
            if value == 'xml':
                return n
        except:
            pass
    raise ValueError, "Could not find the right form."
    

def get_current_bug_id2bug_objs():
    b = mysite.customs.ohloh.mechanize_get(GNOME_LOVE_QUERY)

    # find the one form with ctype XML
    ctype_xml_form_no = find_ctype_xml_form_number(b.forms())

    # Click ze button
    b.select_form(nr=ctype_xml_form_no)
    b.submit()

    # Get a bunch of XML back
    bugzila_elt = lxml.etree.XML(b.response().read())

    ret = {}

    def project_finder_plugin(bug_elt):
        import mysite.search.models
        project_name = bug_elt.xpath('product')[0].text

        ### Special-case a few GNOME-y project names
        gnome2openhatch = {'general': 'GNOME (general)',
                           'website': 'GNOME (website)'}
        if project_name in gnome2openhatch:
            project_name=gnome2openhatch[project_name]
        
        project, _ = mysite.search.models.Project.objects.get_or_create(
            name=project_name)
        return project

    for bug in bugzila_elt.xpath('bug'):
        bug_obj = mysite.customs.miro.bug_elt2bug_object(
            bug, canonical_bug_link_format_string=BUG_URL_PREFIX + '%d',
            gen_project=project_finder_plugin
            )
        bug_id = bug_url2bug_id(bug_obj.canonical_bug_link)
        bug_obj.good_for_newcomers = True
        bug_obj.bite_size_tag_name = 'GNOME-Love'
        ret[bug_id] = bug_obj
        
    return ret

def bug_url2bug_id(url):
    before, after = url.split(BUG_URL_PREFIX)
    return int(after)

def get_remote_bug_ids_already_stored():
    for bug in mysite.search.models.Bug.all_bugs.filter(
        canonical_bug_link__contains=BUG_URL_PREFIX):
        yield bug_url2bug_id(bug.canonical_bug_link)

def grab():
    """Loops over GNOME Bugzilla's list of gnome-love bugs and stores/updates
    them in our DB.
    
    For now, just grab the gnome-love bugs to be kind to their servers."""

    current_bug_id2bug_objs = get_current_bug_id2bug_objs()

    bug_ids = mysite.customs.models.flatten(
        [current_bug_id2bug_objs.keys(), get_remote_bug_ids_already_stored()])

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
