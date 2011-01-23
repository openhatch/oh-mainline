# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2009, 2010 OpenHatch, Inc.
# Copyright (C) 2010 Mark Freeman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import logging
import os
from datetime import timedelta
import datetime
from mysite.customs import ohloh
import urllib2
import urllib
import mysite.customs.github
import mysite.profile.models
from mysite.search.models import Project
from celery.decorators import task
from celery.task import Task
import celery.registry
import time
import random
import traceback
import mysite.profile.search_indexes
import mysite.profile.controllers
import shutil
import staticgenerator

from django.conf import settings
import django.core.cache

def create_citations_from_ohloh_contributor_facts(dia_id, ohloh_results):
    '''Input: A sequence of Ohloh ContributionFact dicts
    and the id of the DataImport they came from.

    Side-effect: Create matching structures in the DB
    and mark our success in the database.'''
    # {{{
    dia = mysite.profile.models.DataImportAttempt.objects.get(id=dia_id)
    person = dia.person
    for ohloh_contrib_info in ohloh_results:
        (project, _) = Project.objects.get_or_create(
                name=ohloh_contrib_info['project'])
        # FIXME: don't import if blacklisted
        (portfolio_entry, _) = mysite.profile.models.PortfolioEntry.objects.get_or_create(
                person=person, project=project)
        citation = mysite.profile.models.Citation.create_from_ohloh_contrib_info(ohloh_contrib_info)
        citation.portfolio_entry = portfolio_entry
        citation.data_import_attempt = dia 
        citation.save_and_check_for_duplicates()

    person.last_polled = datetime.datetime.now()
    dia.completed = True
    dia.save()
    person.save()
    # }}}

def rs_action(dia):
    oh = ohloh.get_ohloh()
    data, web_response = oh.get_contribution_info_by_username(
            dia.query, person=dia.person)
    dia.web_response = web_response
    dia.save()
    return data

def ou_action(dia):
    oh = ohloh.get_ohloh()
    data, web_response = oh.get_contribution_info_by_ohloh_username(
            dia.query, person=dia.person)
    dia.web_response = web_response
    dia.save()
    return data

def do_nothing_because_this_functionality_moved_to_twisted(*args):
    return None # This is moved to Twisted now.

source2actual_action = {
        'gh': do_nothing_because_this_functionality_moved_to_twisted,
        'ga': do_nothing_because_this_functionality_moved_to_twisted,
        'db': do_nothing_because_this_functionality_moved_to_twisted,
        'lp': do_nothing_because_this_functionality_moved_to_twisted,
        'bb': do_nothing_because_this_functionality_moved_to_twisted,
    
        'rs': rs_action,
        'ou': ou_action,
        }

source2result_handler = {
        'db': do_nothing_because_this_functionality_moved_to_twisted,
        'gh': do_nothing_because_this_functionality_moved_to_twisted,
        'ga': do_nothing_because_this_functionality_moved_to_twisted,
        'lp': do_nothing_because_this_functionality_moved_to_twisted,
        'bb': do_nothing_because_this_functionality_moved_to_twisted,

        'rs': create_citations_from_ohloh_contributor_facts,
        'ou': create_citations_from_ohloh_contributor_facts,
        }

class ReindexPerson(Task):
    def run(self, person_id, **kwargs):
        person = mysite.profile.models.Person.objects.get(id=person_id)
        pi = mysite.profile.search_indexes.PersonIndex(person)
        pi.update_object(person)

class GarbageCollectForwarders(Task):
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Started garbage collecting profile email forwarders")
        deleted_any = mysite.profile.models.Forwarder.garbage_collect()
        if deleted_any:
            # Well, in that case, we should purge the staticgenerator-generated cache of the people pages.
            clear_people_page_cache()


class RegeneratePostfixAliasesForForwarder(Task):
    def run(self, **kwargs):
        # Generate the table...
        lines = mysite.profile.models.Forwarder.generate_list_of_lines_for_postfix_table()
        # Save it where Postfix expects it...
        fd = open(settings.POSTFIX_FORWARDER_TABLE_PATH, 'w')
        fd.write('\n'.join(lines))
        fd.close()
        # Update the Postfix forwarder database. Note that we do not need
        # to ask Postfix to reload. Yay!
        # FIXME stop using os.system()
        os.system('/usr/sbin/postmap /etc/postfix/virtual_alias_maps') 

class FetchPersonDataFromOhloh(Task):
    name = "profile.FetchPersonDataFromOhloh"

    def run(self, dia_id, **kwargs):
        """"""
        dia = mysite.profile.models.DataImportAttempt.objects.get(id=dia_id)
        try:
            logger = self.get_logger(**kwargs)
            logger.info("Starting job for <%s>" % dia)
            if dia.completed:
                logger.info("Bailing out job for <%s>" % dia)
                return
            results = source2actual_action[dia.source](dia)
            source2result_handler[dia.source](dia.id, results)
            logger.info("Results: %s" % repr(results))

        except Exception, e:
            # if the task is in debugging mode, bubble-up the exception
            if getattr(self, 'debugging', None):
                raise
            logger.error("Traceback: ")
            logger.error(traceback.format_exc())

            # else let the exception be logged but not bubble up
            dia.completed = True
            dia.failed = True
            dia.save()
            if hasattr(e, 'code'):
                code = str(e.code)
            else:
                code = 'UNKNOWN'
            if hasattr(e, 'geturl'):
                url = str(e.geturl())
            else:
                raise
            logger.error('Dying: ' + code + ' getting ' + url)
            raise ValueError, {'code': code, 'url': url}

try:
    celery.registry.tasks.register(RegeneratePostfixAliasesForForwarder)
    celery.registry.tasks.register(FetchPersonDataFromOhloh)
    celery.registry.tasks.register(ReindexPerson)
    celery.registry.tasks.register(GarbageCollectForwarders)
except celery.registry.AlreadyRegistered:
    pass

@task
def update_person_tag_cache(person__pk):
    person = mysite.profile.models.Person.objects.get(pk=person__pk)
    cache_key = person.get_tag_texts_cache_key()
    django.core.cache.cache.delete(cache_key)
    
    # This getter will populate the cache
    return person.get_tag_texts_for_map()

@task
def update_someones_pf_cache(person__pk):
    person = mysite.profile.models.Person.objects.get(pk=person__pk)
    cache_key = person.get_cache_key_for_projects()
    django.core.cache.cache.delete(cache_key)
    
    # This getter will populate the cache
    return person.get_names_of_nonarchived_projects()

def fill_recommended_bugs_cache():
    logging.info("Filling recommended bugs cache for all people.")
    for person in mysite.profile.models.Person.objects.all():
        fill_one_person_recommend_bugs_cache.apply(person_id=person.id)
    logging.info("Finished filling recommended bugs cache for all people.")

@task
def fill_one_person_recommend_bugs_cache(person_id):
    p = mysite.profile.models.Person.objects.get(id=person_id)
    logging.info("Recommending bugs for %s" % p)
    suggested_searches = p.get_recommended_search_terms() # expensive?
    recommender = mysite.profile.controllers.RecommendBugs(suggested_searches, n=5) # cache fill prep...
    recommender.recommend() # cache fill do it.

def sync_bug_epoch_from_model_then_fill_recommended_bugs_cache():
    logging.info("Syncing bug epoch...")
    # Find the highest bug object modified date
    from django.db.models import Max
    highest_bug_mtime = mysite.search.models.Bug.all_bugs.all().aggregate(
        Max('modified_date')).values()[0]
    epoch = mysite.search.models.Epoch.get_for_model(
        mysite.search.models.Bug)
    # if the epoch is lower, then set the epoch to that value
    if highest_bug_mtime.timetuple() > epoch:
        mysite.search.models.Epoch.bump_for_model(
            mysite.search.models.Bug)
        logging.info("Whee! Bumped the epoch. Guess I'll fill the cache.")
        fill_recommended_bugs_cache()
    logging.info("Done syncing bug epoch.")

@task
def clear_people_page_cache(*args, **kwargs):
    shutil.rmtree(os.path.join(settings.WEB_ROOT,
                               'people'),
                  ignore_errors=True)

def clear_people_page_cache_task(*args, **kwargs):
    return clear_people_page_cache.delay()

def fill_people_page_cache():
    staticgenerator.quick_publish('/people/')

for model in [mysite.profile.models.PortfolioEntry,
              mysite.profile.models.Person,
              mysite.profile.models.Link_Person_Tag]:
    for signal_to_hook in [
        django.db.models.signals.post_save,
        django.db.models.signals.post_delete]:
        signal_to_hook.connect(
            clear_people_page_cache_task,
            sender=model)
