from datetime import timedelta
import datetime
import logging
import mysite.search.models
import mysite.customs.models
from celery.task import Task, PeriodicTask
from celery.registry import tasks

class LookAtOneFedoraBug(Task):
    def run(self, bug_id, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Was asked to look at bug %d in Fedora" % bug_id)
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

        # Is that bug fresh enough?
        if (datetime.datetime.now() - bug_obj.last_polled
            ) > datetime.timedelta(days=1):
            logging.info("Refreshing bug %d from Fedora." %
                         bug_id)
            # if the delta is greater than a day, refresh it.
            mysite.customs.bugtrackers.fedora_fitfinish.reload_bug_obj(bug_obj)
            bug_obj.save()
        logging.info("Finished with %d from Fedora." % bug_id)

class LearnAboutNewFedoraFitAndFinishBugs(PeriodicTask):
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info('Started to learn about new Fedora fit and finish bugs.')
        for bug_id in mysite.customs.bugtrackers.fedora_fitfinish.current_fit_and_finish_bug_ids():
            task = LookAtOneFedoraBug()
            task.delay(bug_id=bug_id)
        logger.info('Finished grabbing the list of Fedora fit and finish bugs.')


class RefreshAllFedoraFitAndFinishBugs(PeriodicTask):
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Starting refreshing all Fedora bugs.")
        for bug in mysite.search.models.Bug.all_bugs.filter(
            canonical_bug_link__contains=
            mysite.customs.bugtrackers.fedora_fitfinish.BUG_URL_PREFIX):
            bug_id = mysite.customs.bugtrackers.bugzilla_general.bug_url2bug_id(bug.canonical_bug_link,
                                                                                BUG_URL_PREFIX=mysite.customs.bugtrackers.fedora_fitfinish.BUG_URL_PREFIX)
            task = LookAtOneFedoraBug()
            task.delay(bug_id=bug_id)

tasks.register(LookAtOneFedoraBug)
tasks.register(LearnAboutNewFedoraFitAndFinishBugs)
tasks.register(RefreshAllFedoraFitAndFinishBugs)
