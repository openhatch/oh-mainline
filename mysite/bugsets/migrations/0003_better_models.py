# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding M2M table for field bugs on 'BugSet'
        db.create_table('bugsets_bugset_bugs', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bugset', models.ForeignKey(orm['bugsets.bugset'], null=False)),
            ('annotatedbug', models.ForeignKey(orm['bugsets.annotatedbug'], null=False))
        ))
        db.create_unique('bugsets_bugset_bugs', ['bugset_id', 'annotatedbug_id'])

        # Deleting field 'AnnotatedBug.id'
        db.delete_column('bugsets_annotatedbug', 'id')

        # Adding field 'AnnotatedBug.title'
        db.add_column('bugsets_annotatedbug', 'title', self.gf('django.db.models.fields.CharField')(default='', max_length=500, blank=True), keep_default=False)

        # Adding field 'AnnotatedBug.description'
        db.add_column('bugsets_annotatedbug', 'description', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'AnnotatedBug.assigned_to'
        db.add_column('bugsets_annotatedbug', 'assigned_to', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'AnnotatedBug.mentor'
        db.add_column('bugsets_annotatedbug', 'mentor', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'AnnotatedBug.language'
        db.add_column('bugsets_annotatedbug', 'language', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'AnnotatedBug.time_estimate'
        db.add_column('bugsets_annotatedbug', 'time_estimate', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'AnnotatedBug.status'
        db.add_column('bugsets_annotatedbug', 'status', self.gf('django.db.models.fields.CharField')(default='u', max_length=1), keep_default=False)

        # Removing M2M table for field bugsets on 'AnnotatedBug'
        db.delete_table('bugsets_annotatedbug_bugsets')

        # Adding M2M table for field tags on 'AnnotatedBug'
        db.create_table('bugsets_annotatedbug_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('annotatedbug', models.ForeignKey(orm['bugsets.annotatedbug'], null=False)),
            ('tag', models.ForeignKey(orm['profile.tag'], null=False))
        ))
        db.create_unique('bugsets_annotatedbug_tags', ['annotatedbug_id', 'tag_id'])

        # Changing field 'AnnotatedBug.url'
        db.alter_column('bugsets_annotatedbug', 'url', self.gf('django.db.models.fields.URLField')(max_length=200, primary_key=True))

        # Adding unique constraint on 'AnnotatedBug', fields ['url']
        db.create_unique('bugsets_annotatedbug', ['url'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'AnnotatedBug', fields ['url']
        db.delete_unique('bugsets_annotatedbug', ['url'])

        # Removing M2M table for field bugs on 'BugSet'
        db.delete_table('bugsets_bugset_bugs')

        # User chose to not deal with backwards NULL issues for 'AnnotatedBug.id'
        raise RuntimeError("Cannot reverse this migration. 'AnnotatedBug.id' and its values cannot be restored.")

        # Deleting field 'AnnotatedBug.title'
        db.delete_column('bugsets_annotatedbug', 'title')

        # Deleting field 'AnnotatedBug.description'
        db.delete_column('bugsets_annotatedbug', 'description')

        # Deleting field 'AnnotatedBug.assigned_to'
        db.delete_column('bugsets_annotatedbug', 'assigned_to')

        # Deleting field 'AnnotatedBug.mentor'
        db.delete_column('bugsets_annotatedbug', 'mentor')

        # Deleting field 'AnnotatedBug.language'
        db.delete_column('bugsets_annotatedbug', 'language')

        # Deleting field 'AnnotatedBug.time_estimate'
        db.delete_column('bugsets_annotatedbug', 'time_estimate')

        # Deleting field 'AnnotatedBug.status'
        db.delete_column('bugsets_annotatedbug', 'status')

        # Adding M2M table for field bugsets on 'AnnotatedBug'
        db.create_table('bugsets_annotatedbug_bugsets', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('annotatedbug', models.ForeignKey(orm['bugsets.annotatedbug'], null=False)),
            ('bugset', models.ForeignKey(orm['bugsets.bugset'], null=False))
        ))
        db.create_unique('bugsets_annotatedbug_bugsets', ['annotatedbug_id', 'bugset_id'])

        # Removing M2M table for field tags on 'AnnotatedBug'
        db.delete_table('bugsets_annotatedbug_tags')

        # Changing field 'AnnotatedBug.url'
        db.alter_column('bugsets_annotatedbug', 'url', self.gf('django.db.models.fields.URLField')(max_length=200))


    models = {
        'bugsets.annotatedbug': {
            'Meta': {'object_name': 'AnnotatedBug'},
            'assigned_to': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'mentor': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'u'", 'max_length': '1'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['profile.Tag']", 'symmetrical': 'False'}),
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
        'profile.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.TagType']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'profile.tagtype': {
            'Meta': {'object_name': 'TagType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['bugsets']
