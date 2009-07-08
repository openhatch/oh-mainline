import datetime
from .profile import ohloh
from .profile.views import exp_scraper_handle_ohloh_results
from .profile.models import Person
from celery.task import Task
from celery.registry import tasks

class FetchPersonDataFromOhloh(Task):
    name = "profile.FetchPersonDataFromOhloh"

    def run(self, username, cooked_data=None, **kwargs):
        person_obj = Person.objects.get(username=username)
        try:
            logger = self.get_logger(**kwargs)
            if cooked_data is None:
                logger.info("Fetching Ohloh data for " + username)
                if person_obj.ohloh_grab_completed:
                    logger.info("Bailing out of Ohloh grab for " + username)
                    return
                oh = ohloh.get_ohloh()
                ohloh_results = oh.get_contribution_info_by_username(username)
            else:
                logger.info("Using cooked Ohloh data for " + username)
                ohloh_results = cooked_data
            
            exp_scraper_handle_ohloh_results(username, ohloh_results)

        except:
            person_obj.poll_on_next_web_view = True
            person_obj.save() # race condition?
            raise

tasks.register(FetchPersonDataFromOhloh)
