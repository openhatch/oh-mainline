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

def reload_bug_obj(bug_obj):
    def project_finder_plugin(bug_elt):
        component = bug_elt.find('component').text
        p, _ = mysite.search.models.Project.objects.get_or_create(name=component)
        # NOTE: If get_or_create() returns a new Project, we're not going
        # to know the primary_language.
        return p

    bug_id = mysite.customs.bugtrackers.bugzilla_general.bug_url2bug_id(
        bug_obj.canonical_bug_link,
        BUG_URL_PREFIX=BUG_URL_PREFIX)
    b = mysite.customs.ohloh.mechanize_get(BUG_URL_PREFIX + '%d&ctype=xml' % bug_id)
    # Grab the bug_elt for this bug...
    bug_elt = lxml.etree.XML(
        b.response().read()).find('bug')
    
    # FIXME: Move bug_elt2bug_object into bugzilla_general
    data = mysite.customs.miro.bug_elt2bug_dict(
        bug_elt,
        canonical_bug_link_format_string=BUG_URL_PREFIX + '%d',
        gen_project=project_finder_plugin)

    for key in data:
        setattr(bug_obj, key, data[key])

    # Bug is from Fedora
    bug_obj.as_appears_in_distribution = 'Fedora'

    # NOTE this makes it bitesized
    # NOTE also that this is a bad place to determine something
    # is good for newcomers.
    bug_obj.good_for_newcomers=True
    return bug_obj

def current_fit_and_finish_bug_ids():
    # This returns a list of bug IDs we should look at
    # that's all the dependencies of this tracking bug. So:
    b = mysite.customs.ohloh.mechanize_get(FIT_AND_FINISH_TRACKING_BUG)
    xml = lxml.etree.XML(b.response().read())
    depends = xml.findall('bug/dependson')
    depends_bug_ids = [int(depend.text) for depend in depends]
    return depends_bug_ids
