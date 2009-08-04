
from south.db import db
from django.db import models
from profile.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'Person.last_touched'
        db.add_column('profile_person', 'last_touched', models.DateTimeField())
        
        # Adding field 'Person.last_polled'
        db.add_column('profile_person', 'last_polled', models.DateTimeField())
        
        # Adding field 'Person.time_record_was_created'
        db.add_column('profile_person', 'time_record_was_created', models.DateTimeField(default=datetime.date(2009, 6, 18)))
        
        # Adding field 'Person.poll_on_next_web_view'
        db.add_column('profile_person', 'poll_on_next_web_view', models.BooleanField(default=True))
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'Person.last_touched'
        db.delete_column('profile_person', 'last_touched')
        
        # Deleting field 'Person.last_polled'
        db.delete_column('profile_person', 'last_polled')
        
        # Deleting field 'Person.time_record_was_created'
        db.delete_column('profile_person', 'time_record_was_created')
        
        # Deleting field 'Person.poll_on_next_web_view'
        db.delete_column('profile_person', 'poll_on_next_web_view')
        
    
    
    models = {
        'profile.person': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'last_polled': ('models.DateTimeField', [], {}),
            'last_touched': ('models.DateTimeField', [], {}),
            'name': ('models.CharField', [], {'max_length': '200'}),
            'password_hash_md5': ('models.CharField', [], {'max_length': '200'}),
            'poll_on_next_web_view': ('models.BooleanField', [], {'default': 'True'}),
            'time_record_was_created': ('models.DateTimeField', [], {'default': 'datetime.date(2009, 6, 18)'}),
            'username': ('models.CharField', [], {'max_length': '200'})
        },
        'search.project': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'profile.persontoprojectrelationship': {
            'description': ('models.TextField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'man_months': ('models.PositiveIntegerField', [], {}),
            'person': ('models.ForeignKey', ["orm['profile.Person']"], {}),
            'person_role': ('models.CharField', [], {'max_length': '200'}),
            'primary_language': ('models.CharField', [], {'max_length': '200'}),
            'project': ('models.ForeignKey', ["orm['search.Project']"], {}),
            'source': ('models.CharField', [], {'max_length': '100'}),
            'tags': ('models.TextField', [], {}),
            'time_finish': ('models.DateTimeField', [], {}),
            'time_record_was_created': ('models.DateTimeField', [], {}),
            'time_start': ('models.DateTimeField', [], {}),
            'url': ('models.URLField', [], {'max_length': '200'})
        }
    }
    
    complete_apps = ['profile']
