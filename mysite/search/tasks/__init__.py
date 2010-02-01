from datetime import timedelta
from mysite.search.models import Project
from mysite.customs.models import RoundupBugTracker
from celery.task import PeriodicTask
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

class GrabPythonBugs(PeriodicTask):
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Started to grab Python 'easy' bugs")
        bug_tracker_name = self.__class__.__name__
        python_core, _ = Project.objects.get_or_create(name='Python', language='Python')
        # FIXME: Do we need this line?
        RoundupBugTracker.objects.filter(name=bug_tracker_name).delete()
        p, _ = RoundupBugTracker.objects.get_or_create(name=bug_tracker_name, project=python_core)
        p.include_these_roundup_bug_statuses = '1,3'
        p.roundup_root_url = 'http://bugs.python.org'
        p.csv_keyword = '6' # Only grab bugs marked "easy"
        p.my_bugs_are_always_good_for_newcomers = True
        p.save()
        p.grab()

class GrabPythonBugsInDocumentation(PeriodicTask):
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Started to grab Python documentation bugs")
        bug_tracker_name = self.__class__.__name__
        python_core, _ = Project.objects.get_or_create(name='Python', language='Python')
        # FIXME: Do we need this line?
        RoundupBugTracker.objects.filter(name=bug_tracker_name).delete()
        p, _ = RoundupBugTracker.objects.get_or_create(name=bug_tracker_name, project=python_core)
        p.include_these_roundup_bug_statuses = '1,3'
        p.roundup_root_url = 'http://bugs.python.org'
        p.my_bugs_concern_just_documentation = True
        p.components = '4'
        p.save()
        p.grab()
        """e.g.,
        http://bugs.python.org/issue?@action=export_csv&@columns=title,id,activity,status
        &@sort=activity&@group=priority&@filter=components,status
        &@pagesize=50&@startwith=0&status=1&components=4"""

tasks.register(GrabMiroBugs)
tasks.register(GrabGnomeLoveBugs)
tasks.register(GrabLaunchpadBugs)
tasks.register(GrabPythonBugs)
tasks.register(GrabPythonBugsInDocumentation)
