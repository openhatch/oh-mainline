
from south.db import db
from django.db import models
from mysite.profile.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Person'
        db.create_table('profile_person', (
            ('id', models.AutoField(primary_key=True)),
            ('name', models.CharField(max_length=200)),
            ('username', models.CharField(max_length=200)),
            ('password_hash_md5', models.CharField(max_length=200)),
        ))
        db.send_create_signal('profile', ['Person'])
        
        # Adding model 'PersonToProjectRelationship'
        db.create_table('profile_persontoprojectrelationship', (
            ('id', models.AutoField(primary_key=True)),
            ('person', models.ForeignKey(orm.Person)),
            ('project', models.ForeignKey(orm['search.Project'])),
            ('person_role', models.CharField(max_length=200)),
            ('tags', models.TextField()),
            ('time_record_was_created', models.DateTimeField()),
            ('url', models.URLField(max_length=200)),
            ('description', models.TextField()),
            ('time_start', models.DateTimeField()),
            ('time_finish', models.DateTimeField()),
            ('man_months', models.PositiveIntegerField()),
            ('primary_language', models.CharField(max_length=200)),
            ('source', models.CharField(max_length=100)),
        ))
        db.send_create_signal('profile', ['PersonToProjectRelationship'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Person'
        db.delete_table('profile_person')
        
        # Deleting model 'PersonToProjectRelationship'
        db.delete_table('profile_persontoprojectrelationship')
        
    
    
    models = {
        'profile.person': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '200'}),
            'password_hash_md5': ('models.CharField', [], {'max_length': '200'}),
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
