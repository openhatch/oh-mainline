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

import logging
import os
import mysite.base.models
import mysite.profile.models
import traceback
import mysite.profile.view_helpers
import shutil
import staticgenerator

import django.conf
import django.core.cache


def do_nothing_because_this_functionality_moved_to_twisted(*args):
    return None  # This is moved to Twisted now.

source2actual_action = {
    'gh': do_nothing_because_this_functionality_moved_to_twisted,
    'ga': do_nothing_because_this_functionality_moved_to_twisted,
    'db': do_nothing_because_this_functionality_moved_to_twisted,
    'lp': do_nothing_because_this_functionality_moved_to_twisted,
    'bb': do_nothing_because_this_functionality_moved_to_twisted,
    'rs': do_nothing_because_this_functionality_moved_to_twisted,
    'ou': do_nothing_because_this_functionality_moved_to_twisted,
}

source2result_handler = {
    'db': do_nothing_because_this_functionality_moved_to_twisted,
    'gh': do_nothing_because_this_functionality_moved_to_twisted,
    'ga': do_nothing_because_this_functionality_moved_to_twisted,
    'lp': do_nothing_because_this_functionality_moved_to_twisted,
    'bb': do_nothing_because_this_functionality_moved_to_twisted,
    'rs': do_nothing_because_this_functionality_moved_to_twisted,
    'ou': do_nothing_because_this_functionality_moved_to_twisted,
}


class GarbageCollectForwarders:

    def run(self, **kwargs):
        logging.info("Started garbage collecting profile email forwarders")
        deleted_any = mysite.profile.models.Forwarder.garbage_collect()
        if deleted_any:
            # Well, in that case, we should purge the staticgenerator-generated
            # cache of the people pages.
            clear_people_page_cache()
        return deleted_any


class RegeneratePostfixAliasesForForwarder:

    def run(self, **kwargs):
        if django.conf.settings.POSTFIX_FORWARDER_TABLE_PATH:
            self.update_table()

    def update_table(self):
        # Generate the table...
        lines = mysite.profile.models.Forwarder.generate_list_of_lines_for_postfix_table(
        )
        # Save it where Postfix expects it...
        fd = open(django.conf.settings.POSTFIX_FORWARDER_TABLE_PATH, 'w')
        fd.write('\n'.join(lines))
        fd.close()
        # Update the Postfix forwarder database. Note that we do not need
        # to ask Postfix to reload. Yay!
        # FIXME stop using os.system()
        if mysite.base.depends.postmap_available():
            os.system('/usr/sbin/postmap /etc/postfix/virtual_alias_maps')


class FetchPersonDataFromOhloh:
    name = "profile.FetchPersonDataFromOhloh"

    def run(self, dia_id, **kwargs):
        dia = mysite.profile.models.DataImportAttempt.objects.get(id=dia_id)
        try:
            logging.info("Starting job for <%s>" % dia)
            if dia.completed:
                logging.info("Bailing out job for <%s>" % dia)
                return
            results = source2actual_action[dia.source](dia)
            source2result_handler[dia.source](dia.id, results)
            logging.info("Results: %s" % repr(results))

        except Exception, e:
            # if the task is in debugging mode, bubble-up the exception
            if getattr(self, 'debugging', None):
                raise
            logging.error("Traceback: ")
            logging.error(traceback.format_exc())

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
            logging.error('Dying: ' + code + ' getting ' + url)
            raise ValueError, {'code': code, 'url': url}


def fill_recommended_bugs_cache():
    logging.info("Filling recommended bugs cache for all people.")
    for person in mysite.profile.models.Person.objects.all():
        fill_one_person_recommend_bugs_cache(person_id=person.id)
    logging.info("Finished filling recommended bugs cache for all people.")


def fill_one_person_recommend_bugs_cache(person_id):
    p = mysite.profile.models.Person.objects.get(id=person_id)
    logging.info("Recommending bugs for %s" % p)
    suggested_searches = p.get_recommended_search_terms()  # expensive?
    # cache fill prep...
    recommender = mysite.profile.view_helpers.RecommendBugs(
        suggested_searches, n=5)
    recommender.recommend()  # cache fill do it.


def sync_bug_timestamp_from_model_then_fill_recommended_bugs_cache():
    logging.info("Syncing bug timestamp...")
    # Find the highest bug object modified date
    from django.db.models import Max
    highest_bug_mtime = mysite.search.models.Bug.all_bugs.all().aggregate(
        Max('modified_date')).values()[0]
    timestamp = mysite.base.models.Timestamp.get_timestamp_for_string(
        str(mysite.search.models.Bug))
    # if the timestamp is lower, then set the timestamp to that value
    if highest_bug_mtime.timetuple() > timestamp.timetuple():
        mysite.base.models.Timestamp.update_timestamp_for_string(
            str(mysite.search.models.Bug))
        logging.info("Whee! Bumped the timestamp. Guess I'll fill the cache.")
        fill_recommended_bugs_cache()
    logging.info("Done syncing bug timestamp.")


def clear_people_page_cache(*args, **kwargs):
    shutil.rmtree(os.path.join(django.conf.settings.WEB_ROOT,
                               'people'),
                  ignore_errors=True)


def fill_people_page_cache():
    staticgenerator.quick_publish('/people/')

for model in [mysite.profile.models.PortfolioEntry,
              mysite.profile.models.Person,
              mysite.profile.models.Link_Person_Tag]:
    for signal_to_hook in [
        django.db.models.signals.post_save,
            django.db.models.signals.post_delete]:
        signal_to_hook.connect(
            clear_people_page_cache,
            sender=model)
