import datetime
from customs import ohloh
from .profile.views import exp_scraper_handle_ohloh_results
from .profile.models import Person, DataImportAttempt
from celery.task import Task
import celery.registry

class FetchPersonDataFromOhloh(Task):
    name = "profile.FetchPersonDataFromOhloh"

    def run(self, dia_id, cooked_data=None, **kwargs):
        dia = DataImportAttempt.objects.get(id=dia_id)
        try:
            logger = self.get_logger(**kwargs)
            logger.info("Querying Ohloh data on username %s into %s" % (
                    dia.query, dia.person.user.username))
            if dia.completed:
                logger.info("Bailing out of Ohloh grab for " + 
                            dia.person.user.username + '/' + 
                            dia.query)
                return
            if cooked_data is None:
                oh = ohloh.get_ohloh()
                ohloh_results = oh.get_contribution_info_by_username(
                    dia.query)
            else:
                logger.info("Using cooked Ohloh data for import of " +
                        "%s data into %s" % (dia.query, 
                                             dia.person.user.username))
                ohloh_results = cooked_data
            
            exp_scraper_handle_ohloh_results(dia.id, ohloh_results)

        except:
            dia.completed = True
            dia.save()
            raise

try:
    celery.registry.tasks.register(FetchPersonDataFromOhloh)
except celery.registry.AlreadyRegistered:
    pass
