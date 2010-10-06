
from south.db import db
from django.db import models
from mysite.customs.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'BugzillaUrl.tracker'
        db.add_column('customs_bugzillaurl', 'tracker', orm['customs.bugzillaurl:tracker'])
        
        # Deleting field 'BugzillaUrl.bugzilla_tracker'
        db.delete_column('customs_bugzillaurl', 'bugzilla_tracker_id')
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'BugzillaUrl.tracker'
        db.delete_column('customs_bugzillaurl', 'tracker_id')
        
        # Adding field 'BugzillaUrl.bugzilla_tracker'
        db.add_column('customs_bugzillaurl', 'bugzilla_tracker', orm['customs.bugzillaurl:bugzilla_tracker'])
        
    
    
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.BugzillaTracker']"}),
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
