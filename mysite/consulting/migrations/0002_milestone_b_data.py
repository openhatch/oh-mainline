
from south.db import db
from django.db import models
from mysite.search.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'Bug.submitter_realname'
        db.add_column('search_bug', 'submitter_realname', models.CharField(max_length=200))
        
        # Adding field 'Project.icon_url'
        db.add_column('search_project', 'icon_url', models.URLField(max_length=200))
        
        # Adding field 'Bug.last_touched'
        db.add_column('search_bug', 'last_touched', models.DateField())
        
        # Adding field 'Bug.importance'
        db.add_column('search_bug', 'importance', models.CharField(max_length=200))
        
        # Adding field 'Bug.people_involved'
        db.add_column('search_bug', 'people_involved', models.IntegerField())
        
        # Adding field 'Bug.last_polled'
        db.add_column('search_bug', 'last_polled', models.DateField())
        
        # Adding field 'Bug.submitter_username'
        db.add_column('search_bug', 'submitter_username', models.CharField(max_length=200))
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'Bug.submitter_realname'
        db.delete_column('search_bug', 'submitter_realname')
        
        # Deleting field 'Project.icon_url'
        db.delete_column('search_project', 'icon_url')
        
        # Deleting field 'Bug.last_touched'
        db.delete_column('search_bug', 'last_touched')
        
        # Deleting field 'Bug.importance'
        db.delete_column('search_bug', 'importance')
        
        # Deleting field 'Bug.people_involved'
        db.delete_column('search_bug', 'people_involved')
        
        # Deleting field 'Bug.last_polled'
        db.delete_column('search_bug', 'last_polled')
        
        # Deleting field 'Bug.submitter_username'
        db.delete_column('search_bug', 'submitter_username')
        
    
    
    models = {
        'search.project': {
            'icon_url': ('models.URLField', [], {'max_length': '200'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', [], {'max_length': '200'}),
            'name': ('models.CharField', [], {'max_length': '200'})
        },
        'search.bug': {
            'description': ('models.TextField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'importance': ('models.CharField', [], {'max_length': '200'}),
            'last_polled': ('models.DateField', [], {}),
            'last_touched': ('models.DateField', [], {}),
            'people_involved': ('models.IntegerField', [], {}),
            'project': ('models.ForeignKey', ['Project'], {}),
            'status': ('models.CharField', [], {'max_length': '200'}),
            'submitter_realname': ('models.CharField', [], {'max_length': '200'}),
            'submitter_username': ('models.CharField', [], {'max_length': '200'}),
            'title': ('models.CharField', [], {'max_length': '200'})
        }
    }
    
    complete_apps = ['search']
