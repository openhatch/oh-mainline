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
    
    def forwards(self, orm):
        
        # Changing field 'Timestamp.key'
        # (to signature: django.db.models.fields.CharField(unique=True, max_length=64))
        db.alter_column('base_timestamp', 'key', orm['base.timestamp:key'])
        
    
    
    def backwards(self, orm):
        
        # Changing field 'Timestamp.key'
        # (to signature: django.db.models.fields.CharField(max_length=255, unique=True))
        db.alter_column('base_timestamp', 'key', orm['base.timestamp:key'])
        
    
    
    models = {
        'base.timestamp': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        }
    }
    
    complete_apps = ['base']
