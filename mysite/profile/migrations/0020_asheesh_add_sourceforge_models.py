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

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Link_SF_Proj_Dude_FM'
        db.create_table('profile_link_sf_proj_dude_fm', (
            ('id', models.AutoField(primary_key=True)),
            ('person', models.ForeignKey(orm.SourceForgePerson)),
            ('project', models.ForeignKey(orm.SourceForgeProject)),
            ('is_admin', models.BooleanField(default=False)),
            ('position', models.CharField(max_length=200)),
            ('date_collected', models.DateTimeField()),
        ))
        db.send_create_signal('profile', ['Link_SF_Proj_Dude_FM'])
        
        # Adding model 'SourceForgeProject'
        db.create_table('profile_sourceforgeproject', (
            ('id', models.AutoField(primary_key=True)),
            ('unixname', models.CharField(max_length=200)),
        ))
        db.send_create_signal('profile', ['SourceForgeProject'])
        
        # Adding model 'SourceForgePerson'
        db.create_table('profile_sourceforgeperson', (
            ('id', models.AutoField(primary_key=True)),
            ('username', models.CharField(max_length=200)),
        ))
        db.send_create_signal('profile', ['SourceForgePerson'])
        
        # Adding field 'ProjectExp.favorite'
        db.add_column('profile_projectexp', 'favorite', models.BooleanField(default=0))
        
        # Changing field 'Person.time_record_was_created'
        db.alter_column('profile_person', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 25, 10, 24, 40, 465787)))
        
        # Changing field 'Link_ProjectExp_Tag.time_record_was_created'
        db.alter_column('profile_link_projectexp_tag', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 25, 10, 24, 40, 858041)))
        
        # Changing field 'Link_Project_Tag.time_record_was_created'
        db.alter_column('profile_link_project_tag', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 25, 10, 24, 40, 948895)))
        
        # Creating unique_together for [person, project] on Link_SF_Proj_Dude_FM.
        db.create_unique('profile_link_sf_proj_dude_fm', ['person_id', 'project_id'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Link_SF_Proj_Dude_FM'
        db.delete_table('profile_link_sf_proj_dude_fm')
        
        # Deleting model 'SourceForgeProject'
        db.delete_table('profile_sourceforgeproject')
        
        # Deleting model 'SourceForgePerson'
        db.delete_table('profile_sourceforgeperson')
        
        # Deleting field 'ProjectExp.favorite'
        db.delete_column('profile_projectexp', 'favorite')
        
        # Changing field 'Person.time_record_was_created'
        db.alter_column('profile_person', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 22, 15, 9, 22, 600497)))
        
        # Changing field 'Link_ProjectExp_Tag.time_record_was_created'
        db.alter_column('profile_link_projectexp_tag', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 22, 15, 9, 22, 531081)))
        
        # Changing field 'Link_Project_Tag.time_record_was_created'
        db.alter_column('profile_link_project_tag', 'time_record_was_created', models.DateTimeField(default=datetime.datetime(2009, 6, 22, 15, 9, 22, 729630)))
        
        # Deleting unique_together for [person, project] on Link_SF_Proj_Dude_FM.
        db.delete_unique('profile_link_sf_proj_dude_fm', ['person_id', 'project_id'])
        
    
    
    models = {
        'profile.person': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'interested_in_working_on': ('models.CharField', [], {'default': "''", 'max_length': '1024'}),
            'last_polled': ('models.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_touched': ('models.DateTimeField', [], {'null': 'True'}),
            'name': ('models.CharField', [], {'max_length': '200'}),
            'password_hash_md5': ('models.CharField', [], {'max_length': '200'}),
            'poll_on_next_web_view': ('models.BooleanField', [], {'default': 'True'}),
            'time_record_was_created': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 25, 10, 24, 42, 27042)'}),
            'username': ('models.CharField', [], {'max_length': '200'})
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
            'tag': ('models.ForeignKey', ["orm['profile.Tag']"], {}),
            'time_record_was_created': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 25, 10, 24, 41, 921862)'})
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
        'profile.link_project_tag': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'project': ('models.ForeignKey', ["orm['search.Project']"], {}),
            'source': ('models.CharField', [], {'max_length': '200'}),
            'tag': ('models.ForeignKey', ["orm['profile.Tag']"], {}),
            'time_record_was_created': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 25, 10, 24, 41, 441781)'})
        },
        'profile.tagtype': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '100'}),
            'prefix': ('models.CharField', [], {'max_length': '20'})
        },
        'profile.projectexp': {
            'Meta': {'unique_together': "[('person','project'),]"},
            'description': ('models.TextField', [], {}),
            'favorite': ('models.BooleanField', [], {'default': '0'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'last_touched': ('models.DateTimeField', [], {'null': 'True'}),
            'man_months': ('models.PositiveIntegerField', [], {'null': 'True'}),
            'person': ('models.ForeignKey', ["orm['profile.Person']"], {}),
            'person_role': ('models.CharField', [], {'max_length': '200'}),
            'primary_language': ('models.CharField', [], {'max_length': '200', 'null': 'True'}),
            'project': ('models.ForeignKey', ["orm['search.Project']"], {}),
            'source': ('models.CharField', [], {'max_length': '100', 'null': 'True'}),
            'time_record_was_created': ('models.DateTimeField', [], {'null': 'True'}),
            'url': ('models.URLField', [], {'max_length': '200', 'null': 'True'})
        }
    }
    
    complete_apps = ['profile']
