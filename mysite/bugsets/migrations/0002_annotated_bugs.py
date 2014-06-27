# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'AnnotatedBug'
        db.create_table('bugsets_annotatedbug', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal('bugsets', ['AnnotatedBug'])

        # Adding M2M table for field bugsets on 'AnnotatedBug'
        db.create_table('bugsets_annotatedbug_bugsets', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('annotatedbug', models.ForeignKey(orm['bugsets.annotatedbug'], null=False)),
            ('bugset', models.ForeignKey(orm['bugsets.bugset'], null=False))
        ))
        db.create_unique('bugsets_annotatedbug_bugsets', ['annotatedbug_id', 'bugset_id'])


    def backwards(self, orm):
        
        # Deleting model 'AnnotatedBug'
        db.delete_table('bugsets_annotatedbug')

        # Removing M2M table for field bugsets on 'AnnotatedBug'
        db.delete_table('bugsets_annotatedbug_bugsets')


    models = {
        'bugsets.annotatedbug': {
            'Meta': {'object_name': 'AnnotatedBug'},
            'bugsets': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bugsets.BugSet']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'bugsets.bugset': {
            'Meta': {'object_name': 'BugSet'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['bugsets']
