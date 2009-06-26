from .profile import ohloh
from .profile.views import exp_scraper_handle_ohloh_results
from celery.task import Task
from celery.registry import tasks

class FetchPersonDataFromOhloh(Task):
    name = "profile.FetchPersonDataFromOhloh"

    def run(self, username, cooked_data=None, **kwargs):
        logger = self.get_logger(**kwargs)
        if cooked_data is None:
            logger.info("Fetching Ohloh data for " + username)
            oh = ohloh.get_ohloh()
            ohloh_results = oh.get_contribution_info_by_username(username)
        else:
            logger.info("Using cooked Ohloh data for " + username)
            ohloh_results = cooked_data
            
        exp_scraper_handle_ohloh_results(username, ohloh_results)
        

tasks.register(FetchPersonDataFromOhloh)
