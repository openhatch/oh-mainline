from datetime import timedelta
from mysite.search.models import Project
from celery.task import PeriodicTask
from celery.registry import tasks
from mysite.search.launchpad_crawl import grab_lp_bugs, lpproj2ohproj
from mysite.search import controllers
import mysite.customs.miro

class GrabLaunchpadBugs(PeriodicTask):
    name = "search.GrabLaunchpadBugs"
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        for lp_project in lpproj2ohproj:
            openhatch_proj = lpproj2ohproj[lp_project]
            logger.info("Started to grab lp.net bugs for %s into %s" % (
                    lp_project, openhatch_project))
            grab_lp_bugs(lp_project=lp_project,
                         openhatch_project=openhatch_project)


class GrabMiroBugs(PeriodicTask):
    name = "search.GrabMiroBugs"
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Started to grab Miro bitesized bugs")
        mysite.customs.miro.grab_miro_bugs()
