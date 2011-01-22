# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2009, 2010 OpenHatch
# Copyright (C) 2010 Mister Deployed
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

import datetime
import logging
import mysite.search.models
import mysite.customs.models
from celery.task import Task, PeriodicTask
import shutil
import os
import os.path
import celery.decorators
import datetime

from django.conf import settings

import mysite.base.helpers

class PopulateProjectIconFromOhloh(Task):
    def run(self, project_id):
        project = mysite.search.models.Project.objects.get(id=project_id)
        project.populate_icon_from_ohloh()
        project.save()
    
class PopulateProjectLanguageFromOhloh(Task):
    def run(self, project_id, **kwargs):
        logger = self.get_logger(**kwargs)
        p = mysite.search.models.Project.objects.get(id=project_id)
        if not p.language:
            oh = mysite.customs.ohloh.get_ohloh()
            try:
                analysis_id = oh.get_latest_project_analysis_id(p.name)
            except KeyError:
                logger.info("No Ohloh analysis found -- early %s" %
                            p.name)
                return
            try:
                data, _ = oh.analysis_id2analysis_data(analysis_id)
            except KeyError:
                logger.info("No Ohloh analysis found for %s" % 
                            p.name)
                return
            if ('main_language_name' in data and
                data['main_language_name']):
                # re-get to minimize race condition time
                p = mysite.search.models.Project.objects.get(id=project_id)
                p.language = data['main_language_name']
                p.save()
                logger.info("Set %s.language to %s" %
                            (p.name, p.language))

### Right now, we cache /search/ pages to disk. We should throw those away
### under two circumstances.
### The first such situation has an entry in profile_hourly_tasks.py

### The second circumstance is if a bug gets marked as closed.
@celery.decorators.task
def clear_search_cache():
    logging.info("Clearing the search cache.")
    mysite.base.helpers.clear_static_cache('search')
