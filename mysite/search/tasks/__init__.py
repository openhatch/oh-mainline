import datetime
import logging
import mysite.search.models
import mysite.customs.models
from celery.task import Task, PeriodicTask
import shutil
import os
import os.path
import celery.decorators
import datetime

from django.conf import settings

import mysite.customs.miro
import mysite.customs.bugtrackers.trac
import mysite.customs.bugtrackers.gnome_love
import mysite.customs.bugtrackers.fedora_fitfinish
import mysite.search.tasks.trac_instances
import mysite.search.tasks.bugzilla_instances
import mysite.search.tasks.launchpad_tasks
import mysite.search.tasks.roundup_instances

class PopulateProjectIconFromOhloh(Task):
    def run(self, project_id):
        project = mysite.search.models.Project.objects.get(id=project_id)
        project.populate_icon_from_ohloh()
        project.save()
    
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

### Right now, we cache /search/ pages to disk. We should throw those away
### under two circumstances.
@celery.decorators.periodic_task(run_every=datetime.timedelta(hours=4))
def periodically_check_if_bug_epoch_eclipsed_the_cached_search_epoch():
    logging.info("Checking if bug epoch eclipsed the cached search epoch")
    cache_time = mysite.search.models.Epoch.get_for_string('search_cache')
    bug_time = mysite.search.models.Epoch.get_for_string('search_cache')
    if cache_time < bug_time:
        clear_search_cache.delay()
        mysite.search.models.Epoch.bump_for_string('search_cache')

### The second circumstance is if a bug gets marked as closed.
@celery.decorators.task
def clear_search_cache():
    logging.info("Clearing the search cache.")
    shutil.rmtree(os.path.join(settings.WEB_ROOT,
                               'search'),
                  ignore_errors=True)
