# This file is part of OpenHatch.
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


from south.db import db
from django.db import models
from mysite.base.models import *

class Migration:
    no_dry_run = True
    
    def forwards(self, orm):
        "Write your forwards migration here"
        for timestamp in orm.Timestamp.objects.all():
            print 'Hashing', timestamp.key
            timestamp.key = Timestamp.hash(timestamp.key)
            timestamp.save()
    
    def backwards(self, orm):
        "Write your backwards migration here"
    
    
    models = {
        'base.timestamp': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        }
    }
    
    complete_apps = ['base']
