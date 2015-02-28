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


logger = logging.getLogger(__name__)


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
        logger.info("Started garbage collecting profile email forwarders")
        deleted_any = mysite.profile.models.Forwarder.garbage_collect()
        if deleted_any:
            # Well, in that case, we should purge the
            # staticgenerator-generated cache of the people pages.
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
        

class FetchPersonDataFromOhloh:
    name = "profile.FetchPersonDataFromOhloh"

    def run(self, **kwargs):
        # if the task is in debugging mode, bubble-up the exception
        if getattr(self, 'debugging', None):
            raise
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
