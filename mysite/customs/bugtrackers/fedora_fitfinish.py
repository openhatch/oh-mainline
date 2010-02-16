import urllib2
import mysite.customs.miro
import mechanize
import mysite.customs.ohloh
import lxml.etree
import mysite.customs.models
import mysite.search.models
import mysite.customs.bugtrackers.bugzilla_general

BUG_URL_PREFIX='https://bugzilla.redhat.com/show_bug.cgi?id='
FIT_AND_FINISH_TRACKING_BUG='https://bugzilla.redhat.com/show_bug.cgi?ctype=xml&id=509829'

def current_bug_id2bug_objs():
    # This returns a list of bug IDs we should look at
    # that's all the dependencies of this tracking bug. So:
    b = mysite.customs.ohloh.mechanize_get(FIT_AND_FINISH_TRACKING_BUG)
    xml = lxml.etree.XML(b.response().read())
    depends = xml.findall('bug/dependson')
    depends_bug_ids = [int(depend.text) for depend in depends]

    def project_finder_plugin(bug_elt):
        p, _ = mysite.search.models.Project.objects.get_or_create(name="Ubuntu")
        return p

    ret = {}
    for bug_id in depends_bug_ids:
        # Grab the bug_elt for this bug...
        bug_elt = lxml.etree.XML(b.open(BUG_URL_PREFIX + '%d&ctype=xml' % bug_id).read()).find('bug')
        
        # FIXME: Move bug_elt2bug_object into bugzilla_general
        bug_obj = mysite.customs.miro.bug_elt2bug_object(
            bug_elt,
            canonical_bug_link_format_string=BUG_URL_PREFIX + '%d',
            gen_project=project_finder_plugin)

        # NOTE this makes it bitesized
        bug_obj.good_for_newcomers=True
        ret[bug_id] = bug_obj
    return ret

def grab():
    '''Loops over Fedora bugs we know about, and stores/updates them
    in our DB.

    For now, we only get the fitandfinish bugs.'''
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
    
