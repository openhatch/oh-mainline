# This file is part of OpenHatch.
# Copyright (C) 2009 OpenHatch, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from south.db import db
from django.db import models
from mysite.profile.models import *
import django.contrib.contenttypes
from django.contrib.contenttypes import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'DataImportAttempt'
        db.create_table('profile_dataimportattempt', (
            ('source', orm['profile.dataimportattempt:source']),
            ('completed', orm['profile.dataimportattempt:completed']),
            ('id', orm['profile.dataimportattempt:id']),
        ))
        db.send_create_signal('profile', ['DataImportAttempt'])
        
        # Adding field 'ProjectExp.should_show_this'
        db.add_column('profile_projectexp', 'should_show_this', orm['profile.projectexp:should_show_this'])
        
        # Adding field 'ProjectExp.data_import_attempt'
        db.add_column('profile_projectexp', 'data_import_attempt', orm['profile.projectexp:data_import_attempt'])
        
        # Changing field 'Person.ohloh_grab_completed'
        # (to signature: django.db.models.fields.BooleanField(default=False, blank=True))
        db.alter_column('profile_person', 'ohloh_grab_completed', orm['profile.person:ohloh_grab_completed'])
        
        # Changing field 'Person.user'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['auth.User'], unique=True))
        db.alter_column('profile_person', 'user_id', orm['profile.person:user'])
        
        # Changing field 'Person.gotten_name_from_ohloh'
        # (to signature: django.db.models.fields.BooleanField(default=False, blank=True))
        db.alter_column('profile_person', 'gotten_name_from_ohloh', orm['profile.person:gotten_name_from_ohloh'])
        
        # Changing field 'Person.poll_on_next_web_view'
        # (to signature: django.db.models.fields.BooleanField(default=True, blank=True))
        db.alter_column('profile_person', 'poll_on_next_web_view', orm['profile.person:poll_on_next_web_view'])
        
        # Changing field 'Link_Person_Tag.person'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['profile.Person']))
        db.alter_column('profile_link_person_tag', 'person_id', orm['profile.link_person_tag:person'])
        
        # Changing field 'Link_Person_Tag.tag'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['profile.Tag']))
        db.alter_column('profile_link_person_tag', 'tag_id', orm['profile.link_person_tag:tag'])
        
        # Changing field 'Tag.tag_type'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['profile.TagType']))
        db.alter_column('profile_tag', 'tag_type_id', orm['profile.tag:tag_type'])
        
        # Changing field 'Link_ProjectExp_Tag.favorite'
        # (to signature: django.db.models.fields.BooleanField(default=False, blank=True))
        db.alter_column('profile_link_projectexp_tag', 'favorite', orm['profile.link_projectexp_tag:favorite'])
        
        # Changing field 'Link_ProjectExp_Tag.project_exp'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['profile.ProjectExp']))
        db.alter_column('profile_link_projectexp_tag', 'project_exp_id', orm['profile.link_projectexp_tag:project_exp'])
        
        # Changing field 'Link_ProjectExp_Tag.tag'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['profile.Tag']))
        db.alter_column('profile_link_projectexp_tag', 'tag_id', orm['profile.link_projectexp_tag:tag'])
        
        # Changing field 'Link_Project_Tag.project'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['search.Project']))
        db.alter_column('profile_link_project_tag', 'project_id', orm['profile.link_project_tag:project'])
        
        # Changing field 'Link_Project_Tag.tag'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['profile.Tag']))
        db.alter_column('profile_link_project_tag', 'tag_id', orm['profile.link_project_tag:tag'])
        
        # Changing field 'Link_SF_Proj_Dude_FM.project'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['profile.SourceForgeProject']))
        db.alter_column('profile_link_sf_proj_dude_fm', 'project_id', orm['profile.link_sf_proj_dude_fm:project'])
        
        # Changing field 'Link_SF_Proj_Dude_FM.person'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['profile.SourceForgePerson']))
        db.alter_column('profile_link_sf_proj_dude_fm', 'person_id', orm['profile.link_sf_proj_dude_fm:person'])
        
        # Changing field 'Link_SF_Proj_Dude_FM.is_admin'
        # (to signature: django.db.models.fields.BooleanField(default=False, blank=True))
        db.alter_column('profile_link_sf_proj_dude_fm', 'is_admin', orm['profile.link_sf_proj_dude_fm:is_admin'])
        
        # Changing field 'ProjectExp.project'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['search.Project']))
        db.alter_column('profile_projectexp', 'project_id', orm['profile.projectexp:project'])
        
        # Changing field 'ProjectExp.person'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['profile.Person']))
        db.alter_column('profile_projectexp', 'person_id', orm['profile.projectexp:person'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'DataImportAttempt'
        db.delete_table('profile_dataimportattempt')
        
        # Deleting field 'ProjectExp.should_show_this'
        db.delete_column('profile_projectexp', 'should_show_this')
        
        # Deleting field 'ProjectExp.data_import_attempt'
        db.delete_column('profile_projectexp', 'data_import_attempt_id')
        
        # Changing field 'Person.ohloh_grab_completed'
        # (to signature: models.BooleanField(default=False))
        db.alter_column('profile_person', 'ohloh_grab_completed', orm['profile.person:ohloh_grab_completed'])
        
        # Changing field 'Person.user'
        # (to signature: models.ForeignKey(orm['auth.User'], unique=True))
        db.alter_column('profile_person', 'user_id', orm['profile.person:user'])
        
        # Changing field 'Person.gotten_name_from_ohloh'
        # (to signature: models.BooleanField(default=False))
        db.alter_column('profile_person', 'gotten_name_from_ohloh', orm['profile.person:gotten_name_from_ohloh'])
        
        # Changing field 'Person.poll_on_next_web_view'
        # (to signature: models.BooleanField(default=True))
        db.alter_column('profile_person', 'poll_on_next_web_view', orm['profile.person:poll_on_next_web_view'])
        
        # Changing field 'Link_Person_Tag.person'
        # (to signature: models.ForeignKey(orm['profile.Person']))
        db.alter_column('profile_link_person_tag', 'person_id', orm['profile.link_person_tag:person'])
        
        # Changing field 'Link_Person_Tag.tag'
        # (to signature: models.ForeignKey(orm['profile.Tag']))
        db.alter_column('profile_link_person_tag', 'tag_id', orm['profile.link_person_tag:tag'])
        
        # Changing field 'Tag.tag_type'
        # (to signature: models.ForeignKey(orm['profile.TagType']))
        db.alter_column('profile_tag', 'tag_type_id', orm['profile.tag:tag_type'])
        
        # Changing field 'Link_ProjectExp_Tag.favorite'
        # (to signature: models.BooleanField(default=False))
        db.alter_column('profile_link_projectexp_tag', 'favorite', orm['profile.link_projectexp_tag:favorite'])
        
        # Changing field 'Link_ProjectExp_Tag.project_exp'
        # (to signature: models.ForeignKey(orm['profile.ProjectExp']))
        db.alter_column('profile_link_projectexp_tag', 'project_exp_id', orm['profile.link_projectexp_tag:project_exp'])
        
        # Changing field 'Link_ProjectExp_Tag.tag'
        # (to signature: models.ForeignKey(orm['profile.Tag']))
        db.alter_column('profile_link_projectexp_tag', 'tag_id', orm['profile.link_projectexp_tag:tag'])
        
        # Changing field 'Link_Project_Tag.project'
        # (to signature: models.ForeignKey(orm['search.Project']))
        db.alter_column('profile_link_project_tag', 'project_id', orm['profile.link_project_tag:project'])
        
        # Changing field 'Link_Project_Tag.tag'
        # (to signature: models.ForeignKey(orm['profile.Tag']))
        db.alter_column('profile_link_project_tag', 'tag_id', orm['profile.link_project_tag:tag'])
        
        # Changing field 'Link_SF_Proj_Dude_FM.project'
        # (to signature: models.ForeignKey(orm['profile.SourceForgeProject']))
        db.alter_column('profile_link_sf_proj_dude_fm', 'project_id', orm['profile.link_sf_proj_dude_fm:project'])
        
        # Changing field 'Link_SF_Proj_Dude_FM.person'
        # (to signature: models.ForeignKey(orm['profile.SourceForgePerson']))
        db.alter_column('profile_link_sf_proj_dude_fm', 'person_id', orm['profile.link_sf_proj_dude_fm:person'])
        
        # Changing field 'Link_SF_Proj_Dude_FM.is_admin'
        # (to signature: models.BooleanField(default=False))
        db.alter_column('profile_link_sf_proj_dude_fm', 'is_admin', orm['profile.link_sf_proj_dude_fm:is_admin'])
        
        # Changing field 'ProjectExp.project'
        # (to signature: models.ForeignKey(orm['search.Project']))
        db.alter_column('profile_projectexp', 'project_id', orm['profile.projectexp:project'])
        
        # Changing field 'ProjectExp.person'
        # (to signature: models.ForeignKey(orm['profile.Person']))
        db.alter_column('profile_projectexp', 'person_id', orm['profile.projectexp:person'])
        
    
    
    models = {
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'profile.person': {
            'gotten_name_from_ohloh': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interested_in_working_on': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'last_polled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'ohloh_grab_completed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'poll_on_next_web_view': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'profile.link_person_tag': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Person']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Tag']"})
        },
        'profile.sourceforgeproject': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'unixname': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'profile.tag': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.TagType']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 19, 13, 39, 2, 840826)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 19, 13, 39, 2, 840676)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'profile.sourceforgeperson': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'profile.link_projectexp_tag': {
            'Meta': {'unique_together': "[('tag', 'project_exp', 'source')]"},
            'favorite': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project_exp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.ProjectExp']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Tag']"})
        },
        'profile.dataimportattempt': {
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        'search.project': {
            'icon_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        'profile.link_sf_proj_dude_fm': {
            'Meta': {'unique_together': "[('person', 'project')]"},
            'date_collected': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.SourceForgePerson']"}),
            'position': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.SourceForgeProject']"})
        },
        'profile.link_project_tag': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Tag']"})
        },
        'profile.tagtype': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'prefix': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'profile.projectexp': {
            'data_import_attempt': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.DataImportAttempt']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'man_months': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Person']"}),
            'person_role': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'primary_language': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'should_show_this': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'})
        }
    }
    
    complete_apps = ['profile']
