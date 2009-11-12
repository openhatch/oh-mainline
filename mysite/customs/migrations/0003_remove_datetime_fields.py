
from south.db import db
from django.db import models
from mysite.customs.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Deleting field 'RoundupBugTracker.datetime_format_string'
        db.delete_column('customs_roundupbugtracker', 'datetime_format_string')
        
        # Deleting field 'RoundupBugTracker.datetime_format_string_with_seconds'
        db.delete_column('customs_roundupbugtracker', 'datetime_format_string_with_seconds')
        
    
    
    def backwards(self, orm):
        
        # Adding field 'RoundupBugTracker.datetime_format_string'
        db.add_column('customs_roundupbugtracker', 'datetime_format_string', orm['customs.roundupbugtracker:datetime_format_string'])
        
        # Adding field 'RoundupBugTracker.datetime_format_string_with_seconds'
        db.add_column('customs_roundupbugtracker', 'datetime_format_string_with_seconds', orm['customs.roundupbugtracker:datetime_format_string_with_seconds'])
        
    
    
    models = {
        'customs.roundupbugtracker': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'include_these_roundup_bug_statuses': ('django.db.models.fields.CharField', [], {'default': "'1'", 'max_length': '255'}),
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
