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
        
        # Adding field 'RoundupBugTracker.keyword'
        db.add_column('customs_roundupbugtracker', 'keyword', orm['customs.roundupbugtracker:keyword'])
        
        # Changing field 'RoundupBugTracker.include_these_roundup_bug_statuses'
        # (to signature: django.db.models.fields.CharField(default='-1,1,2,3,4,5,6', max_length=255))
        db.alter_column('customs_roundupbugtracker', 'include_these_roundup_bug_statuses', orm['customs.roundupbugtracker:include_these_roundup_bug_statuses'])
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'RoundupBugTracker.keyword'
        db.delete_column('customs_roundupbugtracker', 'keyword')
        
        # Changing field 'RoundupBugTracker.include_these_roundup_bug_statuses'
        # (to signature: django.db.models.fields.CharField(default='1', max_length=255))
        db.alter_column('customs_roundupbugtracker', 'include_these_roundup_bug_statuses', orm['customs.roundupbugtracker:include_these_roundup_bug_statuses'])
        
    
    
    models = {
        'customs.roundupbugtracker': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'include_these_roundup_bug_statuses': ('django.db.models.fields.CharField', [], {'default': "'-1,1,2,3,4,5,6'", 'max_length': '255'}),
            'keyword': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '50', 'null': 'True'}),
            'my_bugs_are_always_good_for_newcomers': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'roundup_root_url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'customs.webresponse': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response_headers': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        'search.project': {
            'date_icon_was_fetched_from_ohloh': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_for_search_result': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_smaller_for_badge': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        }
    }
    
    complete_apps = ['customs']
