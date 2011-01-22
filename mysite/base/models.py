# This file is part of OpenHatch.
# Copyright (C) 2009, 2010 OpenHatch
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

from django.db import models
import datetime
import hashlib

class Timestamp(models.Model):

    # This is very simply a mapping from strings to timestamps. Use the method
    # "get_timestamp_for_string" and if there is no timestamp for that string,
    # you'll get Jan 1, 1970 0:00 UTC.
    key = models.CharField(null=False, blank=False, unique=True, max_length=64)
    timestamp = models.DateTimeField(null=False)

    # okay, so strings can be of arbitrary length. But our keys cannot be.
    # therefore, we hash all the keys.
    @staticmethod
    def hash(s):
        return hashlib.sha256(s).hexdigest()

    # Class attribute
    ZERO_O_CLOCK = datetime.datetime.fromtimestamp(0)

    @staticmethod
    def get_timestamp_for_string(s):
        try:
            return Timestamp.objects.get(key=Timestamp.hash(s)).timestamp
        except Timestamp.DoesNotExist:
            return Timestamp.ZERO_O_CLOCK 

    @staticmethod
    def update_timestamp_for_string(s, override_time=None):
        timestamp, _ = Timestamp.objects.get_or_create(key=Timestamp.hash(s), defaults={
            'timestamp': datetime.datetime.utcnow()})
        timestamp.timestamp = override_time or datetime.datetime.utcnow()
        timestamp.save() # definitely!
        return timestamp
