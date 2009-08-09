
from south.db import db
from django.db import models
from mysite.profile.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Link_ProjectExp_Tag'
        db.create_table('profile_link_projectexp_tag', (
            ('id', models.AutoField(primary_key=True)),
            ('tag', models.ForeignKey(orm.Tag)),
            ('project_exp', models.ForeignKey(orm.ProjectExp)),
            ('time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 19, 12, 9, 4, 847921))),
            ('source', models.CharField(max_length=200)),
        ))
        db.send_create_signal('profile', ['Link_ProjectExp_Tag'])
        
        # Adding model 'ProjectExp'
        db.create_table('profile_projectexp', (
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
        db.send_create_signal('profile', ['ProjectExp'])
        
        # Deleting model 'link_persontoprojectrelationship_tag'
        db.delete_table('profile_link_persontoprojectrelationship_tag')
        
        # Deleting model 'persontoprojectrelationship'
        db.delete_table('profile_persontoprojectrelationship')
        
        # Changing field 'Person.time_record_was_created'
        db.alter_column('profile_person', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 19, 12, 9, 4, 301717)))
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Link_ProjectExp_Tag'
        db.delete_table('profile_link_projectexp_tag')
        
        # Deleting model 'ProjectExp'
        db.delete_table('profile_projectexp')
        
        # Adding model 'link_persontoprojectrelationship_tag'
        db.create_table('profile_link_persontoprojectrelationship_tag', (
            ('person_to_project_relationship', models.ForeignKey(orm['profile.PersonToProjectRelationship'])),
            ('source', models.CharField(max_length=200)),
            ('tag', models.ForeignKey(orm['profile.Tag'])),
            ('time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 19, 12, 5, 1, 149232))),
            ('id', models.AutoField(primary_key=True)),
        ))
        db.send_create_signal('profile', ['link_persontoprojectrelationship_tag'])
        
        # Adding model 'persontoprojectrelationship'
        db.create_table('profile_persontoprojectrelationship', (
            ('description', models.TextField()),
            ('tags', models.TextField()),
            ('man_months', models.PositiveIntegerField()),
            ('primary_language', models.CharField(max_length=200)),
            ('id', models.AutoField(primary_key=True)),
            ('time_start', models.DateTimeField()),
            ('source', models.CharField(max_length=100)),
            ('url', models.URLField(max_length=200)),
            ('time_record_was_created', models.DateTimeField()),
            ('project', models.ForeignKey(orm['search.Project'])),
            ('person', models.ForeignKey(orm['profile.Person'])),
            ('time_finish', models.DateTimeField()),
            ('person_role', models.CharField(max_length=200)),
        ))
        db.send_create_signal('profile', ['persontoprojectrelationship'])
        
        # Changing field 'Person.time_record_was_created'
        db.alter_column('profile_person', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 19, 12, 5, 1, 569217)))
        
    
    
    models = {
        'profile.person': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'last_polled': ('models.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_touched': ('models.DateTimeField', [], {}),
            'name': ('models.CharField', [], {'max_length': '200'}),
            'password_hash_md5': ('models.CharField', [], {'max_length': '200'}),
            'poll_on_next_web_view': ('models.BooleanField', [], {'default': 'True'}),
            'time_record_was_created': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 19, 12, 9, 5, 403945)'}),
            'username': ('models.CharField', [], {'max_length': '200'})
        },
        'profile.tag': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'text': ('models.CharField', [], {'max_length': '50'}),
            'type': ('models.CharField', [], {'max_length': '50'})
        },
        'profile.link_projectexp_tag': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'project_exp': ('models.ForeignKey', ["orm['profile.ProjectExp']"], {}),
            'source': ('models.CharField', [], {'max_length': '200'}),
            'tag': ('models.ForeignKey', ["orm['profile.Tag']"], {}),
            'time_record_was_created': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 19, 12, 9, 5, 292717)'})
        },
        'search.project': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'profile.tagtypes': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'prefix': ('models.CharField', [], {'max_length': '20'})
        },
        'profile.projectexp': {
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
        },
        'profile.persontoprojectrelationship': {
            '_stub': True,
            'id': 'models.AutoField(primary_key=True)'
        }
    }
    
    complete_apps = ['profile']
