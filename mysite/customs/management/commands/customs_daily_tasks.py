# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010 OpenHatch, Inc.
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
import urllib2

from django.core.management.base import BaseCommand

import django.conf
django.conf.settings.CELERY_ALWAYS_EAGER = True

import mysite.customs.mechanize_helpers


class Command(BaseCommand):
    args = '<ohloh>'
    help = """Call this once a day to make sure we run periodic network tasks."""

    def check_for_broken_ohloh_links(self):
        things_to_do = []
        for citation in mysite.profile.models.Citation.untrashed.filter(
                data_import_attempt__source__in=('oh', 'rs')):
            def do_it(citation=citation):
                # check citation URL for being a 404
                # if so, remove set the URL to None. Also, log it.
                if citation.url:
                    if mysite.customs.mechanize_helpers.link_works(citation.url):
                        # then we do nothing
                        pass
                    else:
                        # aww shucks, I guess we have to remove it.
                        logging.warning("We had to remove the url %s from the citation whose PK is %d" % (
                            citation.url, citation.pk))
                        citation.url = None
                        citation.save()
            things_to_do.append(do_it)
        return things_to_do

    def handle(self, override_cdt_fns=None, *args, **options):
        if override_cdt_fns:
            cdt_fns = override_cdt_fns
        else:
            cdt_fns = {
                'ohloh': self.check_for_broken_ohloh_links,
            }
        # Which ones do we plan to do this, time we run?
        # Well, if the user supplied arguments on the command line, then put
        # those in the list.
        if args:
            tasks = args
        else:
            # Plan to do them all, since the user did not sub-specify.
            tasks = cdt_fns.keys()

        # Okay, so do the work.
        for key in tasks:
            # Each of these keys returns an iterable of functions to call.
            #
            # We wrap each callable with a big Exception handler so that
            # one failure does not kill the entire process.
            for function in cdt_fns[key]():
                def do_it(function=function, key=key):
                    # Here, we call every one of the worker functions.
                    #
                    # If they fail wih an error, we log the error and proceed
                    # to the next worker function. (The alternative is that we
                    # let the exception bubble-up and make the entire call to the
                    # management command fail.)
                    try:
                        function()
                    except Exception:
                        logging.exception("During %s, the particular importer failed. "
                                          "Skipping it.", key)
                do_it()
