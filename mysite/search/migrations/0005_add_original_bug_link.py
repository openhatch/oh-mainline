
from south.db import db
from django.db import models
from mysite.search.models import *

class Migration:
    
    def forwards(self, orm):
        "Write your forwards migration here"
    
    
    def backwards(self, orm):
        "Write your backwards migration here"
    
    
    models = {
        'search.project': {
            'icon_url': ('models.URLField', [], {'max_length': '200'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', [], {'max_length': '200'}),
            'name': ('models.CharField', [], {'max_length': '200'})
        },
        'search.bug': {
            'canonical_bug_link': ('models.URLField', [], {'max_length': '200'}),
            'date_reported': ('models.DateTimeField', [], {}),
            'description': ('models.TextField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'importance': ('models.CharField', [], {'max_length': '200'}),
            'last_polled': ('models.DateTimeField', [], {}),
            'last_touched': ('models.DateTimeField', [], {}),
            'people_involved': ('models.IntegerField', [], {}),
            'project': ('models.ForeignKey', ['Project'], {}),
            'status': ('models.CharField', [], {'max_length': '200'}),
            'submitter_realname': ('models.CharField', [], {'max_length': '200'}),
            'submitter_username': ('models.CharField', [], {'max_length': '200'}),
            'title': ('models.CharField', [], {'max_length': '200'})
        }
    }
    
    complete_apps = ['search']
