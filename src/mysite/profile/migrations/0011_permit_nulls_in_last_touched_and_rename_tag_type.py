
from south.db import db
from django.db import models
from profile.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'ProjectExp.time_start'
        db.add_column('profile_projectexp', 'time_start', models.DateTimeField(null=True))
        
        # Adding field 'ProjectExp.last_touched'
        db.add_column('profile_projectexp', 'last_touched', models.DateTimeField())
        
        # Adding field 'Tag.tag_type'
        db.add_column('profile_tag', 'tag_type', models.ForeignKey(orm.TagType))
        
        # Adding field 'ProjectExp.time_finish'
        db.add_column('profile_projectexp', 'time_finish', models.DateTimeField(null=True))
        
        # Deleting field 'Tag.type'
        db.delete_column('profile_tag', 'type')
        
        # Deleting field 'ProjectExp.tags'
        db.delete_column('profile_projectexp', 'tags')
        
        # Changing field 'Link_ProjectExp_Tag.time_record_was_created'
        db.alter_column('profile_link_projectexp_tag', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 19, 14, 38, 36, 403378)))
        
        # Changing field 'Person.last_touched'
        db.alter_column('profile_person', 'last_touched', models.DateTimeField(null=True))
        
        # Changing field 'Person.time_record_was_created'
        db.alter_column('profile_person', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 19, 14, 38, 35, 670600)))
        
        # Changing field 'ProjectExp.url'
        db.alter_column('profile_projectexp', 'url', models.URLField(max_length=200, null=True))
        
        # Changing field 'ProjectExp.man_months'
        db.alter_column('profile_projectexp', 'man_months', models.PositiveIntegerField(null=True))
        
        # Changing field 'ProjectExp.source'
        db.alter_column('profile_projectexp', 'source', models.CharField(max_length=100, null=True))
        
        # Changing field 'ProjectExp.primary_language'
        db.alter_column('profile_projectexp', 'primary_language', models.CharField(max_length=200, null=True))
        
        # Changing field 'ProjectExp.time_record_was_created'
        db.alter_column('profile_projectexp', 'time_record_was_created', models.DateTimeField(null=True))
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'ProjectExp.time_start'
        db.delete_column('profile_projectexp', 'time_start')
        
        # Deleting field 'ProjectExp.last_touched'
        db.delete_column('profile_projectexp', 'last_touched')
        
        # Deleting field 'Tag.tag_type'
        db.delete_column('profile_tag', 'tag_type_id')
        
        # Deleting field 'ProjectExp.time_finish'
        db.delete_column('profile_projectexp', 'time_finish')
        
        # Adding field 'Tag.type'
        db.add_column('profile_tag', 'type', models.CharField(max_length=50))
        
        # Adding field 'ProjectExp.tags'
        db.add_column('profile_projectexp', 'tags', models.TextField())
        
        # Changing field 'Link_ProjectExp_Tag.time_record_was_created'
        db.alter_column('profile_link_projectexp_tag', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 19, 12, 50, 22, 475279)))
        
        # Changing field 'Person.last_touched'
        db.alter_column('profile_person', 'last_touched', models.DateTimeField())
        
        # Changing field 'Person.time_record_was_created'
        db.alter_column('profile_person', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 19, 12, 50, 22, 339421)))
        
        # Changing field 'ProjectExp.url'
        db.alter_column('profile_projectexp', 'url', models.URLField(max_length=200))
        
        # Changing field 'ProjectExp.man_months'
        db.alter_column('profile_projectexp', 'man_months', models.PositiveIntegerField())
        
        # Changing field 'ProjectExp.source'
        db.alter_column('profile_projectexp', 'source', models.CharField(max_length=100))
        
        # Changing field 'ProjectExp.primary_language'
        db.alter_column('profile_projectexp', 'primary_language', models.CharField(max_length=200))
        
        # Changing field 'ProjectExp.time_record_was_created'
        db.alter_column('profile_projectexp', 'time_record_was_created', models.DateTimeField())
        
    
    
    models = {
        'profile.person': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'last_polled': ('models.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_touched': ('models.DateTimeField', [], {'null': 'True'}),
            'name': ('models.CharField', [], {'max_length': '200'}),
            'password_hash_md5': ('models.CharField', [], {'max_length': '200'}),
            'poll_on_next_web_view': ('models.BooleanField', [], {'default': 'True'}),
            'time_record_was_created': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 19, 14, 38, 37, 479926)'}),
            'username': ('models.CharField', [], {'max_length': '200'})
        },
        'profile.tag': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'tag_type': ('models.ForeignKey', ["orm['profile.TagType']"], {}),
            'text': ('models.CharField', [], {'max_length': '50'})
        },
        'profile.link_projectexp_tag': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'project_exp': ('models.ForeignKey', ["orm['profile.ProjectExp']"], {}),
            'source': ('models.CharField', [], {'max_length': '200'}),
            'tag': ('models.ForeignKey', ["orm['profile.Tag']"], {}),
            'time_record_was_created': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 19, 14, 38, 37, 340559)'})
        },
        'search.project': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'profile.tagtype': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '100'}),
            'prefix': ('models.CharField', [], {'max_length': '20'})
        },
        'profile.projectexp': {
            'description': ('models.TextField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'last_touched': ('models.DateTimeField', [], {}),
            'man_months': ('models.PositiveIntegerField', [], {'null': 'True'}),
            'person': ('models.ForeignKey', ["orm['profile.Person']"], {}),
            'person_role': ('models.CharField', [], {'max_length': '200'}),
            'primary_language': ('models.CharField', [], {'max_length': '200', 'null': 'True'}),
            'project': ('models.ForeignKey', ["orm['search.Project']"], {}),
            'source': ('models.CharField', [], {'max_length': '100', 'null': 'True'}),
            'time_finish': ('models.DateTimeField', [], {'null': 'True'}),
            'time_record_was_created': ('models.DateTimeField', [], {'null': 'True'}),
            'time_start': ('models.DateTimeField', [], {'null': 'True'}),
            'url': ('models.URLField', [], {'max_length': '200', 'null': 'True'})
        }
    }
    
    complete_apps = ['profile']
