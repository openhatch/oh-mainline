# This file is part of OpenHatch.
# Copyright (C) 2009, 2010 OpenHatch, Inc.
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
        timestamp.save()  # definitely!
        return timestamp

    @staticmethod
    def key_for_model(cls):
        '''This is a helper function that lets the user pass us a model, and
        we generate the key to use.

        It just takes the class name and prepends
        "model last updated " to it.'''
        s = 'model last updated ' + cls.__module__ + '.' + cls.__name__
        return s

# Adjustments to default Django sqlite3 behavior


def activate_foreign_keys(sender, connection, **kwargs):
    """Enable integrity constraint with sqlite."""
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')


def set_asynchronous_for_sqlite(sender, connection, **kwargs):
    """Make sqlite3 be asynchronous. This is risky in case your
    machine crashes, but comes at such a performance boost that
    we do it anyway.

    More info: http://www.sqlite.org/pragma.html#pragma_synchronous """
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA synchronous=OFF;')

from django.db.backends.signals import connection_created
connection_created.connect(activate_foreign_keys)
connection_created.connect(set_asynchronous_for_sqlite)
