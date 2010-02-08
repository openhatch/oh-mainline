from datetime import timedelta
from mysite.search.models import Project
from mysite.customs.models import RoundupBugTracker
from celery.task import Task, PeriodicTask
from celery.registry import tasks
from mysite.search.launchpad_crawl import grab_lp_bugs, lpproj2ohproj
import mysite.customs.miro
import mysite.customs.bugtrackers.gnome_love


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
        for bug_id in RoundupBugTracker.csv_url2bugs(url):
            # enqueue a task to examine this bug
            task = LookAtOneBugInPython(bug_id=bug_id)
            task.delay()
        logger.info("Finished grabbing the list of Python documentation bugs.")

class LearnAboutNewEasyPythonBugs(PeriodicTask):
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Started to grab the list of Python easy bugs.")
        url = 'http://bugs.python.org/issue?status=1%2C3&%40sort=activity&%40columns=id&%40startwith=0&%40group=priority&%40filter=status%2Ckeywords&keywords=6&%40action=export_csv'
        for bug_id in mysite.customs.bugtrackers.python.csv_url2bugs(url):
            # enqueue a task to examine this bug
            task = LookAtOneBugInPython(bug_id=bug_id)
            task.delay()
        logger.info("Finished grabbing the list of Python easy bugs.")

class LookAtOneBugInPython(Task):
    def run(self, bug_id, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Was asked to look at bug %d in Python" % bug_id)
        # If the bug is already in our database, just skip the
        # request.
        url = 'http://bugs.python.org/issue%d' % bug_id
        matching_bugs = Bug.objects.filter(canonical_bug_link=url)
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
            rpt = RoundupBugTracker.objects.get(name='GrabPythonBugs')
        except RoundupBugTracker.DoesNotExist:
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
        python_core, _ = Project.objects.get_or_create(name='Python', language='Python')

        roundup_root_url = 'http://bugs.python.org'
        # Delete all other RoundupBugTracker objects using the same root
        rpts = RoundupBugTracker.objects.filter(roundup_root_url=roundup_root_url)
        for rpt in rpts:
            if rpt.name != bug_tracker_name:
                rpt.delete()

        p, _ = RoundupBugTracker.objects.get_or_create(name=bug_tracker_name, project=python_core)
        p.save()
        p.grab()

tasks.register(GrabMiroBugs)
tasks.register(GrabGnomeLoveBugs)
tasks.register(GrabLaunchpadBugs)
tasks.register(LearnAboutNewEasyPythonBugs)
tasks.register(LearnAboutNewPythonDocumentationBugs)
tasks.register(LookAtOneBugInPython)
tasks.register(GrabPythonBugs)
