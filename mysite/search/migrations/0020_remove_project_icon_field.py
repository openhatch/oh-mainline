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
from mysite.search.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Deleting field 'Project.icon'
        db.delete_column('search_project', 'icon')
        
    
    
    def backwards(self, orm):
        
        # Adding field 'Project.icon'
        db.add_column('search_project', 'icon', orm['search.project:icon'])
        
    
    
    models = {
        'search.bug': {
            'bize_size_tag_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'canonical_bug_link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'date_reported': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'good_for_newcomers': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'importance': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'last_polled': ('django.db.models.fields.DateTimeField', [], {}),
            'last_touched': ('django.db.models.fields.DateTimeField', [], {}),
            'looks_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'people_involved': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'submitter_realname': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'submitter_username': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'search.project': {
            'date_icon_was_fetched_from_ohloh': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'icon_for_profile': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_for_search_result': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_raw': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_smaller_for_badge': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        }
    }
    
    complete_apps = ['search']
