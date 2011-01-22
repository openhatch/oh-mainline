# This file is part of OpenHatch.
# Copyright (C) 2009 OpenHatch
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
    
    no_dry_run = True
    
    def forwards(self, orm):
        "Write your forwards migration here"

        for person in orm.Person.objects.all():
            user, was_user_created = orm['auth.User'].objects.get_or_create(username=person.username)
            person.user = user
            assert user.username == person.username
            if was_user_created:
                user.is_active = False
                user.save()
            person.save()
    
    def backwards(self, orm):
        "Write your backwards migration here"
    
    def backwards(self, orm):
        "Write your backwards migration here"
    
    
    models = {
        'auth.message': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'message': ('models.TextField', ["_('message')"], {}),
            'user': ('models.ForeignKey', ["orm['auth.User']"], {})
        },
        'profile.person': {
            'gotten_name_from_ohloh': ('models.BooleanField', [], {'default': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'interested_in_working_on': ('models.CharField', [], {'default': "''", 'max_length': '1024'}),
            'last_polled': ('models.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_touched': ('models.DateTimeField', [], {'null': 'True'}),
            'name': ('models.CharField', [], {'max_length': '200'}),
            'ohloh_grab_completed': ('models.BooleanField', [], {'default': 'False'}),
            'password_hash_md5': ('models.CharField', [], {'max_length': '200'}),
            'poll_on_next_web_view': ('models.BooleanField', [], {'default': 'True'}),
            'time_record_was_created': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 10, 15, 5, 18, 686204)'}),
            'user': ('models.ForeignKey', ["orm['auth.User']"], {}),
            'username': ('models.CharField', [], {'max_length': '200'})
        },
        'profile.link_person_tag': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'person': ('models.ForeignKey', ["orm['profile.Person']"], {}),
            'source': ('models.CharField', [], {'max_length': '200'}),
            'tag': ('models.ForeignKey', ["orm['profile.Tag']"], {}),
            'time_record_was_created': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 10, 15, 5, 20, 261274)'})
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
            'time_record_was_created': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 10, 15, 5, 16, 979526)'})
        },
        'profile.sourceforgeperson': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'username': ('models.CharField', [], {'max_length': '200'})
        },
        'search.project': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'profile.sourceforgeproject': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'unixname': ('models.CharField', [], {'max_length': '200'})
        },
        'auth.user': {
            'date_joined': ('models.DateTimeField', ["_('date joined')"], {'default': 'datetime.datetime.now'}),
            'email': ('models.EmailField', ["_('e-mail address')"], {'blank': 'True'}),
            'first_name': ('models.CharField', ["_('first name')"], {'max_length': '30', 'blank': 'True'}),
            'groups': ('models.ManyToManyField', ["orm['auth.Group']"], {'blank': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('models.BooleanField', ["_('active')"], {'default': 'True'}),
            'is_staff': ('models.BooleanField', ["_('staff status')"], {'default': 'False'}),
            'is_superuser': ('models.BooleanField', ["_('superuser status')"], {'default': 'False'}),
            'last_login': ('models.DateTimeField', ["_('last login')"], {'default': 'datetime.datetime.now'}),
            'last_name': ('models.CharField', ["_('last name')"], {'max_length': '30', 'blank': 'True'}),
            'password': ('models.CharField', ["_('password')"], {'max_length': '128'}),
            'user_permissions': ('models.ManyToManyField', ["orm['auth.Permission']"], {'blank': 'True'}),
            'username': ('models.CharField', ["_('username')"], {'unique': 'True', 'max_length': '30'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label','codename')", 'unique_together': "(('content_type','codename'),)"},
            'codename': ('models.CharField', ["_('codename')"], {'max_length': '100'}),
            'content_type': ('models.ForeignKey', ["orm['contenttypes.ContentType']"], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', ["_('name')"], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label','model'),)", 'db_table': "'django_content_type'"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
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
        'profile.link_project_tag': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'project': ('models.ForeignKey', ["orm['search.Project']"], {}),
            'source': ('models.CharField', [], {'max_length': '200'}),
            'tag': ('models.ForeignKey', ["orm['profile.Tag']"], {}),
            'time_record_was_created': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 10, 15, 5, 18, 164561)'})
        },
        'profile.tagtype': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '100'}),
            'prefix': ('models.CharField', [], {'max_length': '20'})
        },
        'auth.group': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', ["_('name')"], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('models.ManyToManyField', ["orm['auth.Permission']"], {'blank': 'True'})
        },
        'profile.projectexp': {
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
    
    complete_apps = ['profile', 'auth']
