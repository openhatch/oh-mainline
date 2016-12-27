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
        
        # Adding field 'PortfolioEntry.is_published'
        db.add_column('profile_portfolioentry', 'is_published', orm['profile.portfolioentry:is_published'])
        
        # Changing field 'DataImportAttempt.date_created'
        # (to signature: django.db.models.fields.DateTimeField(default=datetime.datetime(2009, 10, 29, 21, 52, 38, 701735)))
        db.alter_column('profile_dataimportattempt', 'date_created', orm['profile.dataimportattempt:date_created'])
        
        # Changing field 'PortfolioEntry.date_created'
        # (to signature: django.db.models.fields.DateTimeField(default=datetime.datetime(2009, 10, 29, 21, 52, 39, 254639)))
        db.alter_column('profile_portfolioentry', 'date_created', orm['profile.portfolioentry:date_created'])
        
        # Changing field 'Citation.date_created'
        # (to signature: django.db.models.fields.DateTimeField(default=datetime.datetime(2009, 10, 29, 21, 52, 39, 313650)))
        db.alter_column('profile_citation', 'date_created', orm['profile.citation:date_created'])
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'PortfolioEntry.is_published'
        db.delete_column('profile_portfolioentry', 'is_published')
        
        # Changing field 'DataImportAttempt.date_created'
        # (to signature: django.db.models.fields.DateTimeField(default=datetime.datetime(2009, 10, 29, 15, 40, 11, 889042)))
        db.alter_column('profile_dataimportattempt', 'date_created', orm['profile.dataimportattempt:date_created'])
        
        # Changing field 'PortfolioEntry.date_created'
        # (to signature: django.db.models.fields.DateTimeField(default=datetime.datetime(2009, 10, 29, 15, 40, 11, 412825)))
        db.alter_column('profile_portfolioentry', 'date_created', orm['profile.portfolioentry:date_created'])
        
        # Changing field 'Citation.date_created'
        # (to signature: django.db.models.fields.DateTimeField(default=datetime.datetime(2009, 10, 29, 15, 40, 11, 832834)))
        db.alter_column('profile_citation', 'date_created', orm['profile.citation:date_created'])
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'profile.citation': {
            'contributor_role': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'data_import_attempt': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.DataImportAttempt']", 'null': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 10, 29, 21, 52, 40, 124865)'}),
            'distinct_months': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'first_commit_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'languages': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'old_summary': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'portfolio_entry': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.PortfolioEntry']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'})
        },
        'profile.dataimportattempt': {
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 10, 29, 21, 52, 40, 225441)'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Person']"}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        'profile.link_person_tag': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Person']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Tag']"})
        },
        'profile.link_project_tag': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Tag']"})
        },
        'profile.link_projectexp_tag': {
            'Meta': {'unique_together': "[('tag', 'project_exp', 'source')]"},
            'favorite': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project_exp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.ProjectExp']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Tag']"})
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
        'profile.person': {
            'gotten_name_from_ohloh': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interested_in_working_on': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'last_polled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100'}),
            'show_email': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'profile.portfolioentry': {
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 10, 29, 21, 52, 39, 522055)'}),
            'experience_description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Person']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'project_description': ('django.db.models.fields.TextField', [], {})
        },
        'profile.projectexp': {
            'data_import_attempt': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.DataImportAttempt']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'man_months': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'modified': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Person']", 'null': 'True'}),
            'person_role': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'primary_language': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'should_show_this': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'})
        },
        'profile.sourceforgeperson': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '200'})
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
        'profile.tagtype': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'prefix': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'search.project': {
            'date_icon_was_fetched_from_ohloh': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_smaller_for_badge': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        }
    }
    
    complete_apps = ['profile']
