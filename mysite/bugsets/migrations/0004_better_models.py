# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Tag'
        db.create_table('bugsets_tag', (
            ('text', self.gf('django.db.models.fields.CharField')(max_length=200, primary_key=True)),
        ))
        db.send_create_signal('bugsets', ['Tag'])


    def backwards(self, orm):
        
        # Deleting model 'Tag'
        db.delete_table('bugsets_tag')


    models = {
        'bugsets.annotatedbug': {
            'Meta': {'object_name': 'AnnotatedBug'},
            'assigned_to': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'mentor': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'u'", 'max_length': '1'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bugsets.Tag']", 'symmetrical': 'False'}),
            'time_estimate': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'primary_key': 'True'})
        },
        'bugsets.bugset': {
            'Meta': {'object_name': 'BugSet'},
            'bugs': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bugsets.AnnotatedBug']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'bugsets.tag': {
            'Meta': {'object_name': 'Tag'},
            'text': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'})
        }
    }

    complete_apps = ['bugsets']
