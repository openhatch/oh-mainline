import sys
import logging
import os
from datetime import timedelta
import datetime
from mysite.customs import ohloh
import urllib2
import urllib
from mysite.customs import lp_grabber
import mysite.customs.github
import mysite.customs.debianqa
import mysite.profile.models
from mysite.search.models import Project
from celery.decorators import task, periodic_task
from celery.task import Task, PeriodicTask
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

def create_citations_from_launchpad_results(dia_id, lp_results):
    "Input: A dictionary that maps from a project name to information "
    "about that project, e.g. "
    """
         {
             'F-Spot': {
                 'url': 'http://launchpad.net/f-spot',
                 'involvement_types': ['Bug Management', 'Bazaar Branches'],
                 'languages': ['python', 'ruby'],
                 'citation_url': "https://launchpad.net/~paulproteus",
             }
         }
    and the id of the DataImportAttempt they came from.

    Side-effect: Create matching structures in the DB
    and mark our success in the database."""
    # {{{
    dia = mysite.profile.models.DataImportAttempt.objects.get(id=dia_id)
    person = dia.person
    for project_name in lp_results:
        result = lp_results[project_name]
        for involvement_type in result['involvement_types']:

            (project, _) = Project.objects.get_or_create(name=project_name)

            # This works like a 'get_first_or_create'.
            # Sometimes there are more than one existing PortfolioEntry
            # with the details in question.
            # FIXME: This is untested.
            if mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project).count() == 0:
                portfolio_entry = mysite.profile.models.PortfolioEntry(person=person, project=project)
                portfolio_entry.save()
            portfolio_entry = mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project)[0]

            citation = mysite.profile.models.Citation()
            citation.languages = ", ".join(result['languages'])
            citation.contributor_role = involvement_type
            citation.portfolio_entry = portfolio_entry
            citation.data_import_attempt = dia
            citation.url = result['citation_url']
            citation.save_and_check_for_duplicates()

    person.last_polled = datetime.datetime.now()
    person.save()

    dia.completed = True
    dia.save()
    # }}}

def create_citations_from_github_activity_feed_results(dia_id, results):
    return create_citations_from_github_results(dia_id, results,
                                                override_contrib='Collaborated on')

def create_citations_from_github_results(dia_id, results,
                                         override_contrib=None):
    repos, dict_mapping_repos_to_languages = results
    dia = mysite.profile.models.DataImportAttempt.objects.get(id=dia_id)
    person = dia.person
    
    for repo in repos:
        (project, _) = Project.objects.get_or_create(name=repo.name)

        # FIXME: Populate project description, name, etc.

        if mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project).count() == 0:
            portfolio_entry = mysite.profile.models.PortfolioEntry(person=person,
                                             project=project,
                                             project_description=repo.description or '')
            portfolio_entry.save()
        portfolio_entry = mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project)[0]
            
        citation = mysite.profile.models.Citation()
        citation.languages = "" # FIXME ", ".join(result['languages'])
        if repo.fork:
            citation.contributor_role = 'Forked'
        else:
            citation.contributor_role = 'Started'
        if override_contrib:
            citation.contributor_role = override_contrib
        citation.portfolio_entry = portfolio_entry
        citation.data_import_attempt = dia
        citation.url = 'http://github.com/%s/%s/' % (urllib.quote_plus(repo.owner),
                                                     urllib.quote_plus(repo.name))
        citation.save_and_check_for_duplicates()

    person.last_polled = datetime.datetime.now()
    person.save()

    dia.completed = True
    dia.save()

def create_citations_from_debianqa_results(dia_id, results):
    dia = mysite.profile.models.DataImportAttempt.objects.get(id=dia_id)
    person = dia.person

    for package_name, package_description in results:
        (project, _) = Project.objects.get_or_create(name=package_name)

        package_link = 'http://packages.debian.org/src:' + urllib.quote(
            package_name)

        if mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project).count() == 0:
            portfolio_entry = mysite.profile.models.PortfolioEntry(person=person,
                                             project=project,
                                             project_description=package_description)
            portfolio_entry.save()
        portfolio_entry = mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project)[0]
            
        citation = mysite.profile.models.Citation()
        citation.languages = "" # FIXME ", ".join(result['languages'])
        citation.contributor_role='Maintainer'
        citation.portfolio_entry = portfolio_entry
        citation.data_import_attempt = dia
        citation.url = package_link
        citation.save_and_check_for_duplicates()

        # And add a citation to the Debian portfolio entry
        (project, _) = Project.objects.get_or_create(name='Debian GNU/Linux')
        if mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project).count() == 0:
            portfolio_entry = mysite.profile.models.PortfolioEntry(person=person,
                                             project=project,
                                             project_description=
                                             'The universal operating system')
            portfolio_entry.save()
        portfolio_entry = mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project)[0]
        citation = mysite.profile.models.Citation()
        citation.languages = '' # FIXME: ?
        citation.contributor_role='Maintainer of %s' % package_name
        citation.portfolio_entry = portfolio_entry
        citation.data_import_attempt = dia
        citation.url = package_link
        citation.save_and_check_for_duplicates()

    person.last_polled = datetime.datetime.now()
    person.save()

    dia.completed = True
    dia.save()

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

def gh_action(dia):
    # FIXME: We should add a person parameter so that, in the
    # case of "You should retry soon..." messages from the Github
    # API, we notify the user.

    # FIXME: Make web_response objects have a DIA attribute.
    # The way we're doing it now is basically backwards.
    repos = list(mysite.customs.github.repos_by_username(dia.query))
    dict_mapping_repos_to_languages = {}
    for repo in repos:
        key = (repo.owner, repo.name)
        dict_mapping_repos_to_languages[
            key] = '' # mysite.customs.github.find_primary_language_of_repo(
            #github_username=repo.owner,
            #github_reponame=repo.name)
        
    return (repos, dict_mapping_repos_to_languages)

def db_action(dia):
    # Given a dia with a username, check if there are any source packages
    # maintained by that person.
    return list(mysite.customs.debianqa.source_packages_maintained_by(
        dia.query))

def ga_action(dia):
    # FIXME: We should add a person parameter so that, in the
    # case of "You should retry soon..." messages from the Github
    # API, we notify the user.

    # FIXME: Make web_response objects have a DIA attribute.
    # The way we're doing it now is basically backwards.
    repos = list(mysite.customs.github.repos_user_collaborates_on(
                 github_username=dia.query))
    return (repos, {})
    
def lp_action(dia):
    # NB: Don't change the way this is called, because calling it this way
    # permits this function to be mocked when we test it.
    return lp_grabber.get_info_for_launchpad_username(dia.query)

source2actual_action = {
        'rs': rs_action,
        'ou': ou_action,
        'gh': gh_action,
        'ga': ga_action,
        'db': db_action,
        'lp': lp_action
        }

source2result_handler = {
        'rs': create_citations_from_ohloh_contributor_facts,
        'ou': create_citations_from_ohloh_contributor_facts,
        'gh': create_citations_from_github_results,
        'ga': create_citations_from_github_activity_feed_results,
        'db': create_citations_from_debianqa_results,
        'lp': create_citations_from_launchpad_results,
        }

class ReindexPerson(Task):
    def run(self, person_id, **kwargs):
        person = mysite.profile.models.Person.objects.get(id=person_id)
        pi = mysite.profile.search_indexes.PersonIndex(person)
        pi.update_object(person)

class GarbageCollectForwarders(PeriodicTask):
    run_every = timedelta(days=1)
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Started garbage collecting profile email forwarders")
        mysite.profile.models.Forwarder.garbage_collect()


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

@periodic_task(run_every=datetime.timedelta(hours=1))
def fill_recommended_bugs_cache():
    logging.info("Filling recommended bugs cache for all people.")
    for person in mysite.profile.models.Person.objects.all():
        fill_one_person_recommend_bugs_cache.delay(person_id=person.id)
    logging.info("Finished filling recommended bugs cache for all people.")

@task
def fill_one_person_recommend_bugs_cache(person_id):
    p = mysite.profile.models.Person.objects.get(id=person_id)
    logging.info("Recommending bugs for %s" % p)
    suggested_searches = p.get_recommended_search_terms() # expensive?
    recommender = mysite.profile.controllers.RecommendBugs(suggested_searches, n=5) # cache fill prep...
    recommender.recommend() # cache fill do it.

@periodic_task(run_every=datetime.timedelta(hours=1))
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
        fill_recommended_bugs_cache.delay()
    logging.info("Done syncing bug epoch.")

@task
def clear_people_page_cache(*args, **kwargs):
    shutil.rmtree(os.path.join(settings.WEB_ROOT,
                               'people'),
                  ignore_errors=True)

def clear_people_page_cache_task(*args, **kwargs):
    return clear_people_page_cache.delay()

@periodic_task(run_every=datetime.timedelta(minutes=10))
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
