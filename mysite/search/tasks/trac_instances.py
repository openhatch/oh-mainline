import datetime
import logging

from celery.task import Task, PeriodicTask
from celery.registry import tasks
import celery.decorators

import mysite.search.models
import mysite.customs.bugtrackers.trac

### Twisted
class LookAtOneTwistedBug(Task):
    def run(self, bug_id, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Was asked to look at bug %d in Twisted" % bug_id)
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
        if (datetime.datetime.now() - bug_obj.last_polled
            ) > datetime.timedelta(days=1):
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

class LearnAboutNewEasyTwistedBugs(PeriodicTask):
    run_every = datetime.timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        
        logger.info('Started to learn about new Twisted easy bugs.')
        for bug_id in mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                url='http://twistedmatrix.com/trac/query?status=new&status=assigned&status=reopened&format=csv&keywords=%7Eeasy&order=priority')):
            task = LookAtOneTwistedBug()
            task.delay(bug_id=bug_id)
        logger.info('Finished grabbing the list of Twisted easy bugs.')

class RefreshAllTwistedEasyBugs(PeriodicTask):
    run_every = datetime.timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Starting refreshing all easy Twisted bugs.")
        for bug in mysite.search.models.Bug.all_bugs.filter(
            canonical_bug_link__contains=
            'http://twistedmatrix.com/trac/'):
            tb = mysite.customs.bugtrackers.trac.TracBug.from_url(
                bug.canonical_bug_link)
            task = LookAtOneTwistedBug()
            task.delay(bug_id=tb.bug_id)

tasks.register(LearnAboutNewEasyTwistedBugs)
tasks.register(LookAtOneTwistedBug)
tasks.register(RefreshAllTwistedEasyBugs)

@celery.decorators.task
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
    bug.save()
    logging.info("Finished with %d from Sugar Labs." % bug_id)
    
@celery.decorators.periodic_task(run_every=datetime.timedelta(days=1))
def learn_about_new_sugar_easy_bugs():
    logging.info('Started to learn about new Sugar Labs easy bugs.')
    for bug_id in mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
        mysite.customs.bugtrackers.trac.csv_of_bugs(
            url='http://bugs.sugarlabs.org/query?status=new&status=assigned&status=reopened&format=csv&keywords=%7Esugar-love&order=priority')):
        look_at_sugar_labs_bug.delay(bug_id=bug_id)
    logging.info('Finished grabbing the list of Sugar Labs easy bugs.')

@celery.decorators.periodic_task(run_every=datetime.timedelta(days=1))
def refresh_all_sugar_easy_bugs():
    logging.info("Starting refreshing all Sugar bugs.")
    for bug in mysite.search.models.Bug.all_bugs.filter(
        canonical_bug_link__contains=
        'http://bugs.sugarlabs.org/'):
        tb = mysite.customs.bugtrackers.trac.TracBug.from_url(
            bug.canonical_bug_link)
        look_at_sugar_labs_bug.delay(bug_id=tb.bug_id)
