
from south.db import db
from django.db import models
from mysite.search.models import *
import MySQLdb

class Migration:
    
    no_dry_run = True

    def forwards(self, orm):
        
        try:
            # Adding field 'Bug.bize_size_tag_name'
            db.add_column('search_bug', 'bize_size_tag_name', orm['search.bug:bize_size_tag_name'])
        except MySQLdb.OperationalError, args:
            if args[0] == 1060:
                pass
            else:
                raise
        
        # Adding field 'Project.icon_raw'
        db.add_column('search_project', 'icon_raw', orm['search.project:icon_raw'])
        
        # Adding field 'Project.icon_for_profile'
        db.add_column('search_project', 'icon_for_profile', orm['search.project:icon_for_profile'])
        
        # Changing field 'Bug.people_involved'
        # (to signature: django.db.models.fields.IntegerField(null=True))
        db.alter_column('search_bug', 'people_involved', orm['search.bug:people_involved'])

        # Copy contents of 'icon' field into 'icon_raw'.
        for project in orm['search.project'].objects.all():
            project.icon_raw = project.icon
            project.save()
    
    def backwards(self, orm):
        
        # Deleting field 'Bug.bize_size_tag_name'
        db.delete_column('search_bug', 'bize_size_tag_name')
        
        # Deleting field 'Project.icon_raw'
        db.delete_column('search_project', 'icon_raw')
        
        # Deleting field 'Project.icon_for_profile'
        db.delete_column('search_project', 'icon_for_profile')
        
        # Changing field 'Bug.people_involved'
        # (to signature: django.db.models.fields.IntegerField())
        db.alter_column('search_bug', 'people_involved', orm['search.bug:people_involved'])
        
    
    
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
            'icon': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
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
