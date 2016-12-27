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
        
        # Adding model 'BugzillaUrl'
        db.create_table('customs_bugzillaurl', (
            ('id', orm['customs.bugzillaurl:id']),
            ('url', orm['customs.bugzillaurl:url']),
            ('bugzilla_tracker', orm['customs.bugzillaurl:bugzilla_tracker']),
        ))
        db.send_create_signal('customs', ['BugzillaUrl'])
        
        # Adding model 'BugzillaTracker'
        db.create_table('customs_bugzillatracker', (
            ('id', orm['customs.bugzillatracker:id']),
            ('project_name', orm['customs.bugzillatracker:project_name']),
            ('base_url', orm['customs.bugzillatracker:base_url']),
            ('bug_project_name_format', orm['customs.bugzillatracker:bug_project_name_format']),
            ('query_url_type', orm['customs.bugzillatracker:query_url_type']),
            ('bitesized_type', orm['customs.bugzillatracker:bitesized_type']),
            ('bitesized_text', orm['customs.bugzillatracker:bitesized_text']),
            ('documentation_type', orm['customs.bugzillatracker:documentation_type']),
            ('documentation_text', orm['customs.bugzillatracker:documentation_text']),
            ('as_appears_in_distribution', orm['customs.bugzillatracker:as_appears_in_distribution']),
        ))
        db.send_create_signal('customs', ['BugzillaTracker'])
        
        # Deleting model 'roundupbugtracker'
        db.delete_table('customs_roundupbugtracker')
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'BugzillaUrl'
        db.delete_table('customs_bugzillaurl')
        
        # Deleting model 'BugzillaTracker'
        db.delete_table('customs_bugzillatracker')
        
        # Adding model 'roundupbugtracker'
        db.create_table('customs_roundupbugtracker', (
            ('include_these_roundup_bug_statuses', orm['customs.bugzillatracker:include_these_roundup_bug_statuses']),
            ('project', orm['customs.bugzillatracker:project']),
            ('my_bugs_concern_just_documentation', orm['customs.bugzillatracker:my_bugs_concern_just_documentation']),
            ('name', orm['customs.bugzillatracker:name']),
            ('components', orm['customs.bugzillatracker:components']),
            ('csv_keyword', orm['customs.bugzillatracker:csv_keyword']),
            ('roundup_root_url', orm['customs.bugzillatracker:roundup_root_url']),
            ('my_bugs_are_always_good_for_newcomers', orm['customs.bugzillatracker:my_bugs_are_always_good_for_newcomers']),
            ('id', orm['customs.bugzillatracker:id']),
        ))
        db.send_create_signal('customs', ['roundupbugtracker'])
        
    
    
    models = {
        'customs.bugzillatracker': {
            'as_appears_in_distribution': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'bug_project_name_format': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'query_url_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'customs.bugzillaurl': {
            'bugzilla_tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.BugzillaTracker']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'})
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
