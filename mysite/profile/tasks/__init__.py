import datetime
from customs import ohloh
from .profile.views import exp_scraper_handle_ohloh_results
from .profile.models import Person, DataImportAttempt
from celery.task import Task
import celery.registry

def rs_action(dia):
    oh = ohloh.get_ohloh()
    return oh.get_contribution_info_by_username(
            dia.query)

def ou_action(dia):
    oh = ohloh.get_ohloh()
    return oh.get_contribution_info_by_ohloh_username(
            dia.query)

source2actual_action = {
        'ou': ou_action,
        'rs': rs_action}

class FetchPersonDataFromOhloh(Task):
    name = "profile.FetchPersonDataFromOhloh"

    def run(self, dia_id, **kwargs):
        dia = DataImportAttempt.objects.get(id=dia_id)
        try:
            logger = self.get_logger(**kwargs)
            logger.info("Starting job for <%s>" % dia)
            if dia.completed:
                logger.info("Bailing out job for <%s>" % dia)
                return
            ohloh_results = source2actual_action[dia.source](dia)
            exp_scraper_handle_ohloh_results(dia.id, ohloh_results)

        except:
            dia.completed = True
            dia.failed = True
            dia.save()
            raise

try:
    celery.registry.tasks.register(FetchPersonDataFromOhloh)
except celery.registry.AlreadyRegistered:
    pass
