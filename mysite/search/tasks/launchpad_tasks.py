from datetime import timedelta
import datetime
import logging
import mysite.search.models
import mysite.customs.models
from celery.task import Task
from celery.registry import tasks
import celery.decorators
import mysite.search.launchpad_crawl

def refresh_bugs_from_all_indexed_launchpad_projects():
    # Look, ma, a hard-coded table that maps to
    # OpenHatch project names from Launchpad.net project names.
    # TimBL would be proud.
    lpproj2ohproj = { 'lxml': 'lxml',
                      'do': 'GNOME-do',
                      'gwibber': 'Gwibber'}
    for launchpad_project_name in lpproj2ohproj:
        openhatch_project_name = lpproj2ohproj[launchpad_project_name]
        import_bugs_from_one_project(launchpad_project_name,
                                     openhatch_project_name)

@celery.decorators.task
def import_bugs_from_one_project(launchpad_project_name,
                                 openhatch_project_name):
    logging.info("Looking at bugs %s on Launchpad" % launchpad_project_name)
    url = "https://bugs.launchpad.net/%s/+bugs" % launchpad_project_name
    bug_filter = mysite.search.launchpad_crawl.URLBugListFilter()
    # no filtering; dump everything
    l = mysite.search.launchpad_crawl.TextBugList(bug_filter(url))
    # convert elements into Bug objects
    for bug in l:
        openhatch_bug_link = 'https://bugs.launchpad.net/bugs/%d' % (
            bug.bugnumber)
        refresh_one_launchpad_bug(
            canonical_bug_link=openhatch_bug_link,
            openhatch_project_name=openhatch_project_name)

def refresh_all_launchpad_bugs():
    logging.info("Refreshing all Launchpad bugs.")
    for lp_bug in mysite.search.models.Bug.all_bugs.filter(
        canonical_bug_link__startswith='https://bugs.launchpad.net/'):
        refresh_one_launchpad_bug.apply(
            canonical_bug_link=lp_bug.canonical_bug_link,
            openhatch_project_name=None)

@celery.decorators.task
def refresh_one_launchpad_bug(canonical_bug_link,
                              openhatch_project_name):
    logging.info("Checking on %s..." % canonical_bug_link)
    # Either we already have the bug...
    try:
        bug = mysite.search.models.Bug.all_bugs.get(
            canonical_bug_link=canonical_bug_link)
    # ...or we need to create it
    except mysite.search.models.Bug.DoesNotExist:
        bug = mysite.search.models.Bug()
        bug.canonical_bug_link = canonical_bug_link

    if bug.data_is_more_fresh_than_one_day():
        return

    # Okay, so it's stale. Refresh the sucker.
    logging.info("Refreshing %s." % canonical_bug_link)

    # Set the project, if necessary
    if openhatch_project_name is None:
        pass
    else:
        # Get or create the OpenHatch project
        openhatch_project, _ = mysite.search.models.Project.objects.get_or_create(name=openhatch_project_name)
        
        if bug.project_id != openhatch_project.id:
            bug.project = openhatch_project

    # FIXME: One day, look at the bug data to see what project to use.
    # This code incorrectly assumes bugs don't migrate from one project
    # to another.
    prefix = 'https://bugs.launchpad.net/bugs/'
    assert canonical_bug_link.startswith(prefix)
    bug_id_str = canonical_bug_link.split(prefix, 1)[1]
    bug_id = int(bug_id_str)
    tb = mysite.search.launchpad_crawl.TextBug(bug_id)
    data_dict = mysite.search.lpb2json.obj2serializable(tb)
    _, new_data = mysite.search.launchpad_crawl.clean_lp_data_dict(data_dict)
    for key in new_data:
        setattr(bug, key, new_data[key])
    bug.last_polled = datetime.datetime.utcnow()
    bug.save()
