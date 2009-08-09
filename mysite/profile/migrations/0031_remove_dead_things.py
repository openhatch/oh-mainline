
from south.db import db
from django.db import models
from mysite.profile.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Deleting field 'Link_ProjectExp_Tag.time_record_was_created'
        db.delete_column('profile_link_projectexp_tag', 'time_record_was_created')
        
        # Deleting field 'Link_Project_Tag.time_record_was_created'
        db.delete_column('profile_link_project_tag', 'time_record_was_created')
        
        # Deleting field 'Link_Person_Tag.time_record_was_created'
        db.delete_column('profile_link_person_tag', 'time_record_was_created')
        
        # Deleting field 'ProjectExp.last_touched'
        db.delete_column('profile_projectexp', 'last_touched')
        
        # Deleting field 'ProjectExp.time_record_was_created'
        db.delete_column('profile_projectexp', 'time_record_was_created')
        
    
    
    def backwards(self, orm):
        
        # Adding field 'Link_ProjectExp_Tag.time_record_was_created'
        db.add_column('profile_link_projectexp_tag', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 7, 10, 15, 24, 43, 964291)))
        
        # Adding field 'Link_Project_Tag.time_record_was_created'
        db.add_column('profile_link_project_tag', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 7, 10, 15, 24, 45, 653482)))
        
        # Adding field 'Link_Person_Tag.time_record_was_created'
        db.add_column('profile_link_person_tag', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 7, 10, 15, 24, 44, 730680)))
        
        # Adding field 'ProjectExp.last_touched'
        db.add_column('profile_projectexp', 'last_touched', models.DateTimeField(null=True))
        
        # Adding field 'ProjectExp.time_record_was_created'
        db.add_column('profile_projectexp', 'time_record_was_created', models.DateTimeField(null=True))
        
    
    
    models = {
        'profile.person': {
            'gotten_name_from_ohloh': ('models.BooleanField', [], {'default': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'interested_in_working_on': ('models.CharField', [], {'default': "''", 'max_length': '1024'}),
            'ohloh_grab_completed': ('models.BooleanField', [], {'default': 'False'}),
            'poll_on_next_web_view': ('models.BooleanField', [], {'default': 'True'}),
            'user': ('models.ForeignKey', ["orm['auth.User']"], {'unique': 'True'})
        },
        'profile.link_person_tag': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'person': ('models.ForeignKey', ["orm['profile.Person']"], {}),
            'source': ('models.CharField', [], {'max_length': '200'}),
            'tag': ('models.ForeignKey', ["orm['profile.Tag']"], {})
        },
        'profile.tag': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'tag_type': ('models.ForeignKey', ["orm['profile.TagType']"], {}),
            'text': ('models.CharField', [], {'max_length': '50'})
        },
        'profile.link_projectexp_tag': {
            'Meta': {'unique_together': "[('tag','project_exp','source'),]"},
            'favorite': ('models.BooleanField', [], {'default': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'project_exp': ('models.ForeignKey', ["orm['profile.ProjectExp']"], {}),
            'source': ('models.CharField', [], {'max_length': '200'}),
            'tag': ('models.ForeignKey', ["orm['profile.Tag']"], {})
        },
        'profile.sourceforgeperson': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'username': ('models.CharField', [], {'max_length': '200'})
        },
        'profile.link_sf_proj_dude_fm': {
            'Meta': {'unique_together': "[('person','project'),]"},
            'date_collected': ('models.DateTimeField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'is_admin': ('models.BooleanField', [], {'default': 'False'}),
            'person': ('models.ForeignKey', ["orm['profile.SourceForgePerson']"], {}),
            'position': ('models.CharField', [], {'max_length': '200'}),
            'project': ('models.ForeignKey', ["orm['profile.SourceForgeProject']"], {})
        },
        'profile.sourceforgeproject': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'unixname': ('models.CharField', [], {'max_length': '200'})
        },
        'search.project': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'auth.user': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'profile.link_project_tag': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'project': ('models.ForeignKey', ["orm['search.Project']"], {}),
            'source': ('models.CharField', [], {'max_length': '200'}),
            'tag': ('models.ForeignKey', ["orm['profile.Tag']"], {})
        },
        'profile.tagtype': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '100'}),
            'prefix': ('models.CharField', [], {'max_length': '20'})
        },
        'profile.projectexp': {
            'description': ('models.TextField', [], {}),
            'favorite': ('models.BooleanField', [], {'default': '0'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'man_months': ('models.PositiveIntegerField', [], {'null': 'True'}),
            'person': ('models.ForeignKey', ["orm['profile.Person']"], {}),
            'person_role': ('models.CharField', [], {'max_length': '200'}),
            'primary_language': ('models.CharField', [], {'max_length': '200', 'null': 'True'}),
            'project': ('models.ForeignKey', ["orm['search.Project']"], {}),
            'source': ('models.CharField', [], {'max_length': '100', 'null': 'True'}),
            'url': ('models.URLField', [], {'max_length': '200', 'null': 'True'})
        }
    }
    
    complete_apps = ['profile']
