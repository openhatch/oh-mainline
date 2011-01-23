# This file is part of OpenHatch.
# Copyright (C) 2009 OpenHatch, Inc.
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
from mysite.customs.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'WebResponse'
        db.create_table('customs_webresponse', (
            ('id', orm['customs.WebResponse:id']),
            ('text', orm['customs.WebResponse:text']),
            ('url', orm['customs.WebResponse:url']),
            ('status', orm['customs.WebResponse:status']),
            ('response_headers', orm['customs.WebResponse:response_headers']),
        ))
        db.send_create_signal('customs', ['WebResponse'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'WebResponse'
        db.delete_table('customs_webresponse')
        
    
    
    models = {
        'customs.webresponse': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response_headers': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.TextField', [], {})
        }
    }
    
    complete_apps = ['customs']
