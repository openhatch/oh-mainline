from datetime import timedelta
import datetime
import logging
import mysite.search.models
import mysite.customs.models
from celery.task import Task, PeriodicTask
from celery.registry import tasks
from mysite.search.launchpad_crawl import grab_lp_bugs, lpproj2ohproj
import mysite.customs.miro
import mysite.customs.bugtrackers.gnome_love
import mysite.customs.bugtrackers.fedora_fitfinish

class GrabLaunchpadBugs(PeriodicTask):
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        for lp_project in lpproj2ohproj:
            openhatch_proj = lpproj2ohproj[lp_project]
            logger.info("Started to grab lp.net bugs for %s into %s" % (
                    lp_project, openhatch_proj))
            grab_lp_bugs(lp_project=lp_project,
                         openhatch_project=openhatch_proj)


class GrabMiroBugs(PeriodicTask):
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Started to grab Miro bitesized bugs")
        mysite.customs.miro.grab_miro_bugs()

class GrabGnomeLoveBugs(PeriodicTask):
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Started to grab GNOME Love bugs")
        mysite.customs.bugtrackers.gnome_love.grab()

class LearnAboutNewPythonDocumentationBugs(PeriodicTask):
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Started to grab the list of Python documentation bugs.")
        url = 'http://bugs.python.org/issue?status=1%2C3&%40sort=activity&%40columns=id&%40startwith=0&%40group=priority&%40filter=status%2Ccomponents&components=4&%40action=export_csv'
        for bug_id in mysite.customs.models.RoundupBugTracker.csv_url2bugs(url):
            # enqueue a task to examine this bug
            task = LookAtOneBugInPython()
            task.delay(bug_id=bug_id)
        logger.info("Finished grabbing the list of Python documentation bugs.")

class LearnAboutNewEasyPythonBugs(PeriodicTask):
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Started to grab the list of Python easy bugs.")
        url = 'http://bugs.python.org/issue?status=1%2C3&%40sort=activity&%40columns=id&%40startwith=0&%40group=priority&%40filter=status%2Ckeywords&keywords=6&%40action=export_csv'
        for bug_id in mysite.customs.models.RoundupBugTracker.csv_url2bugs(url):
            # enqueue a task to examine this bug
            task = LookAtOneBugInPython()
            task.delay(bug_id=bug_id)
        logger.info("Finished grabbing the list of Python easy bugs.")

class LookAtOneBugInPython(Task):
    def run(self, bug_id, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Was asked to look at bug %d in Python" % bug_id)
        # If the bug is already in our database, just skip the
        # request.
        url = 'http://bugs.python.org/issue%d' % bug_id
        matching_bugs = mysite.search.models.Bug.all_bugs.filter(
            canonical_bug_link=url)
        if matching_bugs:
            logger.info("We already know about %d in Python." % bug_id)
            return
        # Okay, so we must create it.
        # Note that creating it here is enough for the other background
        # refreshing daemon to pick up on it when it next
        # calls self.grab(). However, we do an eager refresh here.

        # FIXME: We should pay attention to the last time we refreshed it
        # to avoid hammering remote servers.

        try:
            rpt = mysite.customs.models.RoundupBugTracker.objects.get(name='GrabPythonBugs')
        except mysite.customs.models.RoundupBugTracker.DoesNotExist:
            logger.info("Could not find a matching Python bug tracker. Bailing.")
            return

        bug = rpt.create_bug_object_for_remote_bug_id(bug_id)

        # If there is already a bug with this canonical_bug_link in the DB, just delete it.
        bugs_this_one_replaces = mysite.search.models.Bug.all_bugs.filter(canonical_bug_link=bug.canonical_bug_link)
        for delete_me in bugs_this_one_replaces:
            delete_me.delete()
        bug.save()
        logger.info("Successfully loaded %d in as a Python bug." % bug_id)

class GrabPythonBugs(PeriodicTask):
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Started to grab Python 'easy' bugs")
        bug_tracker_name = self.__class__.__name__
        python_core, _ = mysite.search.models.Project.objects.get_or_create(name='Python', language='Python')

        roundup_root_url = 'http://bugs.python.org'
        # Delete all other mysite.customs.models.RoundupBugTracker objects using the same root
        rpts = mysite.customs.models.RoundupBugTracker.objects.filter(roundup_root_url=roundup_root_url)
        for rpt in rpts:
            if rpt.name != bug_tracker_name:
                rpt.delete()

        p, _ = mysite.customs.models.RoundupBugTracker.objects.get_or_create(name=bug_tracker_name, project=python_core)
        p.save()
        p.grab()

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


class LearnAboutNewEasyTwistedBugs(PeriodicTask):
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        
        logger.info('Started to learn about new Twisted easy bugs.')
        for bug_id in mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.twisted_csv_of_easy_bugs()):
            task = LookAtOneTwistedBug()
            task.delay(bug_id=bug_id)
        logger.info('Finished grabbing the list of Twisted easy bugs.')

class LookAtOneTwistedBug(Task):
    def run(self, bug_id, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Was asked to look at bug %d in Twisted" % bug_id)
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

class PopulateProjectLanguageFromOhloh(Task):
    def run(self, project_id, **kwargs):
        logger = self.get_logger(**kwargs)
        p = mysite.search.models.Project.objects.get(id=project_id)
        if not p.language:
            oh = mysite.customs.ohloh.get_ohloh()
            try:
                analysis_id = oh.get_latest_project_analysis_id(p.name)
            except KeyError:
                logger.info("No Ohloh analysis found -- early %s" %
                            p.name)
                return
            try:
                data, _ = oh.analysis_id2analysis_data(analysis_id)
            except KeyError:
                logger.info("No Ohloh analysis found for %s" % 
                            p.name)
                return
            if ('main_language_name' in data and
                data['main_language_name']):
                # re-get to minimize race condition time
                p = mysite.search.models.Project.objects.get(id=project_id)
                p.language = data['main_language_name']
                p.save()
                logger.info("Set %s.language to %s" %
                            (p.name, p.language))

tasks.register(GrabMiroBugs)
tasks.register(GrabGnomeLoveBugs)
tasks.register(GrabLaunchpadBugs)
tasks.register(LearnAboutNewEasyPythonBugs)
tasks.register(LearnAboutNewPythonDocumentationBugs)
tasks.register(LookAtOneBugInPython)
tasks.register(GrabPythonBugs)
tasks.register(LookAtOneFedoraBug)
tasks.register(LearnAboutNewFedoraFitAndFinishBugs)
tasks.register(RefreshAllFedoraFitAndFinishBugs)
tasks.register(PopulateProjectLanguageFromOhloh)
