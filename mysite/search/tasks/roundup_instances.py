import datetime
import logging
import mysite.search.models
import mysite.customs.models
from celery.task import Task, PeriodicTask
import shutil
import inspect
import os
import os.path
import celery.decorators
import datetime
import mysite.customs.bugtrackers.roundup_general

from django.conf import settings

@celery.decorators.task
def look_at_one_bug_in_mercurial(bug_id):
    # Instantiate Roundup Tracker
    roundup = mysite.customs.bugtrackers.roundup_general.MercurialTracker()
    roundup.create_bug_object_for_remote_bug_id_if_necessary(bug_id)

@celery.decorators.periodic_task(run_every=datetime.timedelta(days=1))
def learn_about_new_mercurial_easy_and_documentation_bugs():
    logging.info("Started " + inspect.stack()[1][3])
    roundup = mysite.customs.bugtrackers.roundup_general.MercurialTracker()
    for bug_id in roundup.generate_list_of_bug_ids_to_look_at():
        look_at_one_bug_in_mercurial.delay(bug_id=bug_id)
    logging.info("Finished " + inspect.stack()[1][3])

@celery.decorators.periodic_task(run_every=datetime.timedelta(days=1))
def refresh_all_mercurial_bugs():
    logging.info("Starting refreshing all Mercurial bugs.")
    roundup = mysite.customs.bugtrackers.roundup_general.MercurialTracker()
    for bug_id in roundup.get_remote_bug_ids_already_stored():
        look_at_one_bug_in_mercurial.delay(bug_id=bug_id)


