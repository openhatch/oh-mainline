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
from mysite.search.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Project'
        db.create_table('search_project', (
            ('id', models.AutoField(primary_key=True)),
            ('language', models.CharField(max_length=200)),
            ('name', models.CharField(max_length=200)),
        ))
        db.send_create_signal('search', ['Project'])
        
        # Adding model 'Bug'
        db.create_table('search_bug', (
            ('project', models.ForeignKey(orm.Project)),
            ('status', models.CharField(max_length=200)),
            ('description', models.TextField()),
            ('id', models.AutoField(primary_key=True)),
            ('title', models.CharField(max_length=200)),
        ))
        db.send_create_signal('search', ['Bug'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Project'
        db.delete_table('search_project')
        
        # Deleting model 'Bug'
        db.delete_table('search_bug')
        
    
    
    models = {
        'search.project': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', [], {'max_length': '200'}),
            'name': ('models.CharField', [], {'max_length': '200'})
        },
        'search.bug': {
            'description': ('models.TextField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'project': ('models.ForeignKey', ['Project'], {}),
            'status': ('models.CharField', [], {'max_length': '200'}),
            'title': ('models.CharField', [], {'max_length': '200'})
        }
    }
    
    complete_apps = ['search']
