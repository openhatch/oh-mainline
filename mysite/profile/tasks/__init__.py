import sys
import datetime
from mysite.customs import ohloh
import urllib2
from mysite.customs import lp_grabber
import mysite.customs.github
from mysite.profile.models import Person, DataImportAttempt, Citation, PortfolioEntry
from mysite.search.models import Project
from celery.task import Task
import celery.registry
import time
import random
import traceback

def create_citations_from_ohloh_contributor_facts(dia_id, ohloh_results):
    '''Input: A sequence of Ohloh ContributionFact dicts
    and the id of the DataImport they came from.

    Side-effect: Create matching structures in the DB
    and mark our success in the database.'''
    # {{{
    dia = DataImportAttempt.objects.get(id=dia_id)
    person = dia.person
    for ohloh_contrib_info in ohloh_results:
        (project, _) = Project.objects.get_or_create(
                name=ohloh_contrib_info['project'])
        # FIXME: don't import if blacklisted
        (portfolio_entry, _) = PortfolioEntry.objects.get_or_create(
                person=person, project=project)
        citation = Citation.create_from_ohloh_contrib_info(ohloh_contrib_info)
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
    dia = DataImportAttempt.objects.get(id=dia_id)
    person = dia.person
    for project_name in lp_results:
        result = lp_results[project_name]
        for involvement_type in result['involvement_types']:

            (project, _) = Project.objects.get_or_create(name=project_name)

            # This works like a 'get_first_or_create'.
            # Sometimes there are more than one existing PortfolioEntry
            # with the details in question.
            # FIXME: This is untested.
            if PortfolioEntry.objects.filter(person=person, project=project).count() == 0:
                portfolio_entry = PortfolioEntry(person=person, project=project)
                portfolio_entry.save()
            portfolio_entry = PortfolioEntry.objects.filter(person=person, project=project)[0]

            citation = Citation()
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

def create_citations_from_github_contributor_facts(dia_id, results):
    pass

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

def github_action(dia):
    # FIXME: We should add a person parameter so that, in the
    # case of "You should retry soon..." messages from the Github
    # API, we notify the user.

    # FIXME: Make web_response objects have a DIA attribute.
    # The way we're doing it now is basically backwards.
    data, web_response = mysite.customs.github.info_by_username(dia.query)
    
def lp_action(dia):
    # NB: Don't change the way this is called, because calling it this way
    # permits this function to be mocked when we test it.
    return lp_grabber.get_info_for_launchpad_username(dia.query)

source2actual_action = {
        'rs': rs_action,
        'ou': ou_action,
        'gh': github_action,
        'lp': lp_action
        }

source2result_handler = {
        'rs': create_citations_from_ohloh_contributor_facts,
        'ou': create_citations_from_ohloh_contributor_facts,
        'gh': create_citations_from_github_contributor_facts,
        'lp': create_citations_from_launchpad_results,
        }

class FetchPersonDataFromOhloh(Task):
    name = "profile.FetchPersonDataFromOhloh"

    def run(self, dia_id, **kwargs):
        """"""
        dia = DataImportAttempt.objects.get(id=dia_id)
        try:
            logger = self.get_logger(**kwargs)
            logger.info("Starting job for <%s>" % dia)
            if dia.completed:
                logger.info("Bailing out job for <%s>" % dia)
                return
            results = source2actual_action[dia.source](dia)
            source2result_handler[dia.source](dia.id, results)
            logger.info("Results: %s" % results)

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
                url = 'UNKNOWN'
            logger.error('Dying: ' + code + ' getting ' + url)
            raise ValueError, {'code': code, 'url': url}

try:
    celery.registry.tasks.register(FetchPersonDataFromOhloh)
except celery.registry.AlreadyRegistered:
    pass
