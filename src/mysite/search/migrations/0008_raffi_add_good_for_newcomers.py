
from south.db import db
from django.db import models
from mysite.search.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'Bug.good_for_newcomers'
        db.add_column('search_bug', 'good_for_newcomers', models.BooleanField(default=False))
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'Bug.good_for_newcomers'
        db.delete_column('search_bug', 'good_for_newcomers')
        
    
    
    models = {
        'search.project': {
            'icon_url': ('models.URLField', [], {'max_length': '200'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', [], {'max_length': '200'}),
            'name': ('models.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        'search.bug': {
            'canonical_bug_link': ('models.URLField', [], {'max_length': '200'}),
            'date_reported': ('models.DateTimeField', [], {}),
            'description': ('models.TextField', [], {}),
            'good_for_newcomers': ('models.BooleanField', [], {'default': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'importance': ('models.CharField', [], {'max_length': '200'}),
            'last_polled': ('models.DateTimeField', [], {}),
            'last_touched': ('models.DateTimeField', [], {}),
            'people_involved': ('models.IntegerField', [], {}),
            'project': ('models.ForeignKey', ["orm['search.Project']"], {}),
            'status': ('models.CharField', [], {'max_length': '200'}),
            'submitter_realname': ('models.CharField', [], {'max_length': '200'}),
            'submitter_username': ('models.CharField', [], {'max_length': '200'}),
            'title': ('models.CharField', [], {'max_length': '200'})
        }
    }
    
    complete_apps = ['search']
