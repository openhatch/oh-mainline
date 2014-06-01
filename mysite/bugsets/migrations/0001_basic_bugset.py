# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'BugSet'
        db.create_table('bugsets_bugset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('bugsets', ['BugSet'])


    def backwards(self, orm):
        
        # Deleting model 'BugSet'
        db.delete_table('bugsets_bugset')


    models = {
        'bugsets.bugset': {
            'Meta': {'object_name': 'BugSet'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['bugsets']
