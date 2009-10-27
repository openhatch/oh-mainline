
from south.db import db
from django.db import models
from mysite.search.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'Project.icon'
        db.add_column('search_project', 'icon', orm['search.project:icon'])
        
        # Adding field 'Project.date_icon_was_fetched_from_ohloh'
        db.add_column('search_project', 'date_icon_was_fetched_from_ohloh', orm['search.project:date_icon_was_fetched_from_ohloh'])
        
        # Changing field 'Bug.project'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['search.Project']))
        db.alter_column('search_bug', 'project_id', orm['search.bug:project'])
        
        # Changing field 'Bug.good_for_newcomers'
        # (to signature: django.db.models.fields.BooleanField(default=False, blank=True))
        db.alter_column('search_bug', 'good_for_newcomers', orm['search.bug:good_for_newcomers'])
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'Project.icon'
        db.delete_column('search_project', 'icon')
        
        # Deleting field 'Project.date_icon_was_fetched_from_ohloh'
        db.delete_column('search_project', 'date_icon_was_fetched_from_ohloh')
        
        # Changing field 'Bug.project'
        # (to signature: models.ForeignKey(orm['search.Project']))
        db.alter_column('search_bug', 'project_id', orm['search.bug:project'])
        
        # Changing field 'Bug.good_for_newcomers'
        # (to signature: models.BooleanField(default=False))
        db.alter_column('search_bug', 'good_for_newcomers', orm['search.bug:good_for_newcomers'])
        
    
    
    models = {
        'search.bug': {
            'canonical_bug_link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'date_reported': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'good_for_newcomers': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'importance': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'last_polled': ('django.db.models.fields.DateTimeField', [], {}),
            'last_touched': ('django.db.models.fields.DateTimeField', [], {}),
            'people_involved': ('django.db.models.fields.IntegerField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'submitter_realname': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'submitter_username': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'search.project': {
            'date_icon_was_fetched_from_ohloh': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        }
    }
    
    complete_apps = ['search']
