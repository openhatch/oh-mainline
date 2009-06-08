
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
