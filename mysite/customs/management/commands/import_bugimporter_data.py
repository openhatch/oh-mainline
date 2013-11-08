# This file is part of OpenHatch.
# Copyright (C) 2012 OpenHatch, Inc.
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

from django.core.management.base import BaseCommand
import mysite.customs.core_bugimporters
import yaml
from django.utils import simplejson
import logging


def jsonlines_decoder(f):
    for line in f:
        if line.endswith('\n'):
            line = line[:-1]
        try:
            yield simplejson.loads(line)
        except Exception:
            logging.exception("simplejson decode failed")
            logging.error("repr(line) was: %s", repr(line))
            continue


class Command(BaseCommand):
    args = '<yaml/json_file yaml/json_file ...>'
    help = "Call this command with YAML/JSON files to load into the Bug table"

    def handle(self, *args, **options):
        for filename in args:
            with open(filename) as f:
                if filename.endswith('.json'):
                    bug_dicts = simplejson.load(f)
                elif filename.endswith('.jsonlines'):
                    bug_dicts = jsonlines_decoder(f)
                else:
                    # assume YAML
                    s = f.read()
                    bug_dicts = yaml.loads(s)
                for bug_dict in bug_dicts:
                    mysite.customs.core_bugimporters.import_one_bug_item(
                        bug_dict)
