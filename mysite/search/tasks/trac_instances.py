import datetime
import logging

import mysite.search.models
import mysite.customs.bugtrackers.trac

### Twisted
def look_at_one_twisted_bug(bug_id):
    """Import one Twisted bug. bug_id is the ticket number in the bug's URL."""
    logging.info("Was asked to look at bug %d in Twisted" % bug_id)
    tb = mysite.customs.bugtrackers.trac.TracBug(
        bug_id=bug_id,
        BASE_URL='http://twistedmatrix.com/trac/')

    bug_url = tb.as_bug_specific_url()

    # If bug is already in our database, and we looked at
    # it within the past day, skip the request.
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

    # Is that bug fresh enough?
    if bug_obj.data_is_more_fresh_than_one_day():
        logging.info("Skipping! It's fresh.")
        return
    else: # it is stale.
        logging.info("Refreshing bug %d from Twisted." %
                     bug_id)
        # if the delta is greater than a day, refresh it.
        data = tb.as_data_dict_for_bug_object()
        for key in data:
            value = data[key]
            setattr(bug_obj, key, value)
        # And the project...
        if not bug_obj.project_id:
            project, _ = mysite.search.models.Project.objects.get_or_create(name='Twisted')
            bug_obj.project = project
        bug_obj.save()
    logging.info("Finished with %d from Twisted." % bug_id)

def learn_about_new_easy_twisted_bugs():
    logging.info('Started to learn about new Twisted easy bugs.')
    for bug_id in mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
        mysite.customs.bugtrackers.trac.csv_of_bugs(
            url='http://twistedmatrix.com/trac/query?status=new&status=assigned&status=reopened&format=csv&keywords=%7Eeasy&order=priority')):
        look_at_one_twisted_bug(bug_id=bug_id)
    logging.info('Finished grabbing the list of Twisted easy bugs.')

def refresh_all_twisted_bugs():
    logging.info("Starting refreshing all easy Twisted bugs.")
    all_such_bugs = mysite.search.models.Bug.all_bugs.filter(
        canonical_bug_link__contains=
        'http://twistedmatrix.com/trac/')
    logging.info("All %d of them." % all_such_bugs.count())

    for bug in all_such_bugs:
        tb = mysite.customs.bugtrackers.trac.TracBug.from_url(
            bug.canonical_bug_link)
        look_at_one_twisted_bug(bug_id=tb.bug_id)

def look_at_sugar_labs_bug(bug_id):
    logging.info("Looking at bug %d in Sugar Labs" % bug_id)
    tb = mysite.customs.bugtrackers.trac.TracBug(
        bug_id=bug_id,
        BASE_URL='http://bugs.sugarlabs.org/')
    bug_url = tb.as_bug_specific_url()
    
    try:
        bug = mysite.search.models.Bug.all_bugs.get(
            canonical_bug_link=bug_url)
    except mysite.search.models.Bug.DoesNotExist:
        bug = mysite.search.models.Bug(canonical_bug_link = bug_url)

    # Hopefully, the bug is so fresh it needs no refreshing.
    if bug.data_is_more_fresh_than_one_day():
        logging.info("Bug is fresh. Doing nothing!")
        return # sweet

    # Okay, fine, we need to actually refresh it.
    logging.info("Refreshing bug %d from Sugar Labs." %
                 bug_id)
    data = tb.as_data_dict_for_bug_object()
    for key in data:
        value = data[key]
        setattr(bug, key, value)

    # And the project...
    project_from_tb, _ = mysite.search.models.Project.objects.get_or_create(name=tb.component)
    if bug.project_id != project_from_tb.id:
        bug.project = project_from_tb
    bug.last_polled = datetime.datetime.utcnow()
    bug.save()
    logging.info("Finished with %d from Sugar Labs." % bug_id)
    
def learn_about_new_sugar_easy_bugs():
    logging.info('Started to learn about new Sugar Labs easy bugs.')
    for bug_id in mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
        mysite.customs.bugtrackers.trac.csv_of_bugs(
            url='http://bugs.sugarlabs.org/query?status=new&status=assigned&status=reopened&format=csv&keywords=%7Esugar-love&order=priority')):
        look_at_sugar_labs_bug(bug_id=bug_id)
    logging.info('Finished grabbing the list of Sugar Labs easy bugs.')

def refresh_all_sugar_easy_bugs():
    logging.info("Starting refreshing all Sugar bugs.")
    for bug in mysite.search.models.Bug.all_bugs.filter(
        canonical_bug_link__contains=
        'http://bugs.sugarlabs.org/'):
        tb = mysite.customs.bugtrackers.trac.TracBug.from_url(
            bug.canonical_bug_link)
        look_at_sugar_labs_bug(bug_id=tb.bug_id)

class TracBugTracker(object):
    enabled = False

    def __init__(self, base_url, project_name, bitesized_keyword):
        self.base_url = base_url
        self.project_name = project_name
        self.bitesized_keyword = bitesized_keyword

    def update(self):
        logging.info("Started refreshing all %s bugs." % self.project_name)

        # First, go through and refresh all the bugs specifically marked
        # as bugs to look at.

        must_look_at_these = self.generate_list_of_bug_ids_to_look_at()
        for bug_id in must_look_at_these:
            self.refresh_one_bug_id(bug_id)

        # Then, refresh them all
        self.refresh_all_bugs()

    def refresh_all_bugs(self):
        for bug in mysite.search.models.Bug.all_bugs.filter(
            canonical_bug_link__contains=self.base_url):
            tb = mysite.customs.bugtrackers.trac.TracBug.from_url(
                bug.canonical_bug_link)
            self.refresh_one_bug_id(tb.bug_id)

    def refresh_one_bug_id(self, bug_id):
        tb = mysite.customs.bugtrackers.trac.TracBug(
            bug_id=bug_id,
            BASE_URL=self.base_url)
        bug_url = tb.as_bug_specific_url()
    
        try:
            bug = mysite.search.models.Bug.all_bugs.get(
                canonical_bug_link=bug_url)
        except mysite.search.models.Bug.DoesNotExist:
            bug = mysite.search.models.Bug(canonical_bug_link = bug_url)

        # Hopefully, the bug is so fresh it needs no refreshing.
        if bug.data_is_more_fresh_than_one_day():
            logging.info("Bug is fresh. Doing nothing!")
            return # sweet

        # Okay, fine, we need to actually refresh it.
        logging.info("Refreshing bug %d from %s." %
                     (bug_id, self.project_name))
        data = tb.as_data_dict_for_bug_object()

        for key in data:
            value = data[key]
            setattr(bug, key, value)

        # If the bug has the relevant keyword, mark it as good_for_newcomers
        ### FIXME: This done by hard-coding in the TracBug class.

        # And save the project onto it
        project_from_tb, _ = mysite.search.models.Project.objects.get_or_create(name=tb.component)
        if bug.project_id != project_from_tb.id:
            bug.project = project_from_tb
        bug.last_polled = datetime.datetime.utcnow()
        bug.save()
        logging.info("Finished with %d from %s." % (bug_id, self.project_name))
            
class TahoeLafsTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Tahoe-LAFS',
                                base_url='http://tahoe-lafs.org/trac/tahoe-lafs/',
                                bitesized_keyword='easy')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://tahoe-lafs.org/trac/tahoe-lafs/query?status=assigned&status=new&status=reopened&max=10000&reporter=~&col=id&col=summary&col=keywords&col=reporter&col=status&col=owner&col=type&col=priority&col=milestone&keywords=~&owner=~&desc=1&order=id&format=csv'))
