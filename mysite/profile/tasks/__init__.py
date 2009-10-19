import datetime
from mysite.customs import ohloh
import urllib2
from mysite.customs import lp_grabber
from mysite.profile.views import ohloh_contributor_facts_to_project_exps, create_project_exps_from_launchpad_contributor_facts
from mysite.profile.models import Person, DataImportAttempt
from celery.task import Task
import celery.registry
import time
import random

def rs_action(dia):
    oh = ohloh.get_ohloh()
    if dia.query == 'paulproteus':
        time.sleep(random.randrange(3, 8))
        ret = [{'man_months': 1,
                'primary_language': u'shell script',
                'project': u'ccHost',
                'project_homepage_url': u'http://wiki.creativecommons.org/CcHost'}]
        return ret
    if dia.query == 'asheesh@asheesh.org':
        time.sleep(random.randrange(3, 8))
        ret = [{'man_months': 1,
                'primary_language': u'Python',
                'project': u'playerpiano',
                'project_homepage_url': u'http://code.google.com/p/playerpiano'}]
        return ret
    return oh.get_contribution_info_by_username(
            dia.query)

def ou_action(dia):
    oh = ohloh.get_ohloh()
    if dia.query == 'paulproteus':
        time.sleep(random.randrange(0, 2))
        return [{'man_months': 1,
                 'primary_language': u'shell script',
                 'project': u'ccHost',
                 'project_homepage_url': u'http://wiki.creativecommons.org/CcHost'}]
    if dia.query == 'asheesh@asheesh.org':
        time.sleep(random.randrange(0, 2))
        return []
    return oh.get_contribution_info_by_ohloh_username(
            dia.query)

def lp_action(dia):
    # NB: Don't change the way this is called, because calling it this way
    # permits this function to be mocked when we test it.
    # FIXME: Is that true?

    return lp_grabber.get_info_for_launchpad_username(dia.query)

source2actual_action = {
        'rs': rs_action,
        'ou': ou_action,
        'lp': lp_action
        }

source2result_handler = {
        'rs': ohloh_contributor_facts_to_project_exps,
        'ou': ohloh_contributor_facts_to_project_exps,
        'lp': create_project_exps_from_launchpad_contributor_facts,
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
