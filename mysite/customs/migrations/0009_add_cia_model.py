
from south.db import db
from django.db import models
from mysite.customs.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'RecentMessageFromCIA'
        db.create_table('customs_recentmessagefromcia', (
            ('id', orm['customs.recentmessagefromcia:id']),
            ('committer_identifier', orm['customs.recentmessagefromcia:committer_identifier']),
            ('project_name', orm['customs.recentmessagefromcia:project_name']),
            ('path', orm['customs.recentmessagefromcia:path']),
            ('version', orm['customs.recentmessagefromcia:version']),
            ('message', orm['customs.recentmessagefromcia:message']),
            ('module', orm['customs.recentmessagefromcia:module']),
            ('branch', orm['customs.recentmessagefromcia:branch']),
            ('time_received', orm['customs.recentmessagefromcia:time_received']),
        ))
        db.send_create_signal('customs', ['RecentMessageFromCIA'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'RecentMessageFromCIA'
        db.delete_table('customs_recentmessagefromcia')
        
    
    
    models = {
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
        'customs.roundupbugtracker': {
            'components': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '50', 'null': 'True'}),
            'csv_keyword': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '50', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'include_these_roundup_bug_statuses': ('django.db.models.fields.CharField', [], {'default': "'-1,1,2,3,4,5,6'", 'max_length': '255'}),
            'my_bugs_are_always_good_for_newcomers': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'my_bugs_concern_just_documentation': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
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
            'icon_for_profile': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_for_search_result': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_raw': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_smaller_for_badge': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True'})
        }
    }
    
    complete_apps = ['customs']
