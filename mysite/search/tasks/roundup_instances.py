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
import mysite.customs.bugtrackers.roundup_general

from django.conf import settings

@celery.decorators.task
def look_at_one_bug_in_mercurial(bug_id):
    # Instantiate Roundup Tracker
    roundup = mysite.customs.bugtrackers.roundup_general.MercurialTracker()
    roundup.create_bug_object_for_remote_bug_id_if_necessary(bug_id)

def learn_about_new_mercurial_easy_and_documentation_bugs():
    name = 'learning about new mercurial easy and documentation bugs'
    logging.info("Started " + name)
    roundup = mysite.customs.bugtrackers.roundup_general.MercurialTracker()
    for bug_id in roundup.generate_list_of_bug_ids_to_look_at():
        look_at_one_bug_in_mercurial.apply(bug_id=bug_id)
    logging.info("Finished " + name)

def refresh_all_mercurial_bugs():
    logging.info("Starting refreshing all Mercurial bugs.")
    roundup = mysite.customs.bugtrackers.roundup_general.MercurialTracker()
    count = 0
    for bug_id in roundup.get_remote_bug_ids_already_stored():
        look_at_one_bug_in_mercurial(bug_id=bug_id)
        count += 1
    logging.info("Okay, looked at %d bugs from Mercurial." % count)
