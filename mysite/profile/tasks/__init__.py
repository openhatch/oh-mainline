import datetime
from customs import ohloh
from .profile.views import exp_scraper_handle_ohloh_results
from .profile.models import Person
from celery.task import Task
import celery.registry

class FetchPersonDataFromOhloh(Task):
    name = "profile.FetchPersonDataFromOhloh"

    def run(self, username, commit_username, cooked_data=None, **kwargs):
        person_obj = Person.objects.get(user__username=username)
        try:
            logger = self.get_logger(**kwargs)
            if cooked_data is None:
                logger.info("Querying Ohloh data on username %s into %s" % (
                    commit_username, username))
                if person_obj.ohloh_grab_completed:
                    logger.info("Bailing out of Ohloh grab for " + username
                            + "/" + commit_username)
                    return
                oh = ohloh.get_ohloh()
                ohloh_results = oh.get_contribution_info_by_username(
                        commit_username)
            else:
                logger.info("Using cooked Ohloh data for import of " +
                        "%s data into %s" % (commit_username, username))
                ohloh_results = cooked_data
            
            exp_scraper_handle_ohloh_results(username, ohloh_results)

        except:
            person_obj.poll_on_next_web_view = True
            person_obj.save() # race condition?
            raise

try:
    celery.registry.tasks.register(FetchPersonDataFromOhloh)
except celery.registry.AlreadyRegistered:
    pass
