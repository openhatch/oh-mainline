from datetime import timedelta
import datetime
import logging
import mysite.search.models
import mysite.customs.models
from celery.task import Task, PeriodicTask
from celery.registry import tasks
from mysite.search.launchpad_crawl import grab_lp_bugs, lpproj2ohproj
import mysite.customs.miro
import mysite.customs.bugtrackers.trac
import mysite.customs.bugtrackers.gnome_love
import mysite.customs.bugtrackers.fedora_fitfinish
import mysite.search.tasks.trac_instances
import mysite.search.tasks.bugzilla_instances

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

tasks.register(GrabLaunchpadBugs)
tasks.register(LearnAboutNewEasyPythonBugs)
tasks.register(LearnAboutNewPythonDocumentationBugs)
tasks.register(LookAtOneBugInPython)
tasks.register(GrabPythonBugs)
tasks.register(PopulateProjectLanguageFromOhloh)
