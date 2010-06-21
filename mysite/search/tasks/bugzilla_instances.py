import datetime
import logging

import mysite.search.models

def look_at_one_fedora_bug(bug_id):
    logging.info("Was asked to look at bug %d in Fedora" % bug_id)
    # If bug is already in our database, and we looked at
    # it within the past day, skip the request.
    bug_url = mysite.customs.bugtrackers.bugzilla_general.bug_id2bug_url(
        bug_id=bug_id,
        BUG_URL_PREFIX=mysite.customs.bugtrackers.fedora_fitfinish.BUG_URL_PREFIX)

    try:
        bug_obj = mysite.search.models.Bug.all_bugs.get(
            canonical_bug_link=bug_url)
    except mysite.search.models.Bug.MultipleObjectsReturned:
        # delete all but the first
        bug_objs = mysite.search.models.Bug.all_bugs.filter(
            canonical_bug_link=bug_url)
        bug_obj = bug_objs[0]
        for stupid_dup in bug_objs[1:]:
            stupid_dup.delete()

    except mysite.search.models.Bug.DoesNotExist:
        bug_obj = mysite.search.models.Bug(
            canonical_bug_link=bug_url)

    # Is that bug fresh enough to skip?
    if bug_obj.data_is_more_fresh_than_one_day():
        logging.info("Bug is fresh! Skipping.")
        return
    # if the delta is greater than a day, refresh it.
    mysite.customs.bugtrackers.fedora_fitfinish.reload_bug_obj(bug_obj)
    bug_obj.save()
    logging.info("Finished with %d from Fedora." % bug_id)

def learn_about_new_fedora_fit_and_finish_bugs():
    logging.info('Started to learn about new Fedora fit and finish bugs.')
    for bug_id in mysite.customs.bugtrackers.fedora_fitfinish.current_fit_and_finish_bug_ids():
        look_at_one_fedora_bug(bug_id=bug_id)
    logging.info('Finished grabbing the list of Fedora fit and finish bugs.')

def refresh_all_fedora_fit_and_finish_bugs():
    logging.info("Starting refreshing all Fedora bugs.")
    all_such_bugs = mysite.search.models.Bug.all_bugs.filter(
        canonical_bug_link__contains=
        mysite.customs.bugtrackers.fedora_fitfinish.BUG_URL_PREFIX)
    logging.info("All %d of them." % all_such_bugs.count())

    for bug in all_such_bugs:
        bug_id = mysite.customs.bugtrackers.bugzilla_general.bug_url2bug_id(
            bug.canonical_bug_link,
            BUG_URL_PREFIX=mysite.customs.bugtrackers.fedora_fitfinish.BUG_URL_PREFIX)
        look_at_one_fedora_bug(bug_id=bug_id)

