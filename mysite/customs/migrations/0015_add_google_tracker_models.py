# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
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
        
        # Adding model 'GoogleTracker'
        db.create_table('customs_googletracker', (
            ('id', orm['customs.googletracker:id']),
            ('project_name', orm['customs.googletracker:project_name']),
            ('google_name', orm['customs.googletracker:google_name']),
            ('bitesized_type', orm['customs.googletracker:bitesized_type']),
            ('bitesized_text', orm['customs.googletracker:bitesized_text']),
            ('documentation_type', orm['customs.googletracker:documentation_type']),
            ('documentation_text', orm['customs.googletracker:documentation_text']),
        ))
        db.send_create_signal('customs', ['GoogleTracker'])
        
        # Adding model 'GoogleQuery'
        db.create_table('customs_googlequery', (
            ('id', orm['customs.googlequery:id']),
            ('label', orm['customs.googlequery:label']),
            ('description', orm['customs.googlequery:description']),
            ('tracker', orm['customs.googlequery:tracker']),
        ))
        db.send_create_signal('customs', ['GoogleQuery'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'GoogleTracker'
        db.delete_table('customs_googletracker')
        
        # Deleting model 'GoogleQuery'
        db.delete_table('customs_googlequery')
        
    
    
    models = {
        'customs.bugzillatracker': {
            'as_appears_in_distribution': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10'}),
            'bug_project_name_format': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'query_url_type': ('django.db.models.fields.CharField', [], {'default': "'xml'", 'max_length': '20'})
        },
        'customs.bugzillaurl': {
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.BugzillaTracker']"}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'})
        },
        'customs.googlequery': {
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.GoogleTracker']"})
        },
        'customs.googletracker': {
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10'}),
            'google_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        'customs.recentmessagefromcia': {
            'branch': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'committer_identifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'module': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'project_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'time_received': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'customs.webresponse': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response_headers': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.TextField', [], {})
        }
    }
    
    complete_apps = ['customs']
