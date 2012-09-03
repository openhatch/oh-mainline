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

class Command(BaseCommand):
    args = '<yaml_file yaml_file ...>'
    help = "Call this command and pass it YAML files to load into the Bug table"

    def handle(self, *args, **options):
        for yaml_file in args:
            with open(yaml_file) as f:
                s = f.read()
                bug_dicts = yaml.load(s)
            for bug_dict in bug_dicts:
                mysite.customs.core_bugimporters.import_one_bug_item(bug_dict)
