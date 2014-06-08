# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Skill'
        db.create_table('bugsets_skill', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
        ))
        db.send_create_signal('bugsets', ['Skill'])

        # Adding M2M table for field bugs on 'BugSet'
        db.create_table('bugsets_bugset_bugs', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bugset', models.ForeignKey(orm['bugsets.bugset'], null=False)),
            ('annotatedbug', models.ForeignKey(orm['bugsets.annotatedbug'], null=False))
        ))
        db.create_unique('bugsets_bugset_bugs', ['bugset_id', 'annotatedbug_id'])

        # Adding field 'AnnotatedBug.title'
        db.add_column('bugsets_annotatedbug', 'title', self.gf('django.db.models.fields.CharField')(default='', max_length=500, blank=True), keep_default=False)

        # Adding field 'AnnotatedBug.description'
        db.add_column('bugsets_annotatedbug', 'description', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'AnnotatedBug.assigned_to'
        db.add_column('bugsets_annotatedbug', 'assigned_to', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'AnnotatedBug.mentor'
        db.add_column('bugsets_annotatedbug', 'mentor', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'AnnotatedBug.time_estimate'
        db.add_column('bugsets_annotatedbug', 'time_estimate', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'AnnotatedBug.status'
        db.add_column('bugsets_annotatedbug', 'status', self.gf('django.db.models.fields.CharField')(default='u', max_length=1), keep_default=False)

        # Removing M2M table for field bugsets on 'AnnotatedBug'
        db.delete_table('bugsets_annotatedbug_bugsets')

        # Adding M2M table for field skills on 'AnnotatedBug'
        db.create_table('bugsets_annotatedbug_skills', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('annotatedbug', models.ForeignKey(orm['bugsets.annotatedbug'], null=False)),
            ('skill', models.ForeignKey(orm['bugsets.skill'], null=False))
        ))
        db.create_unique('bugsets_annotatedbug_skills', ['annotatedbug_id', 'skill_id'])

        # Adding unique constraint on 'AnnotatedBug', fields ['url']
        db.create_unique('bugsets_annotatedbug', ['url'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'AnnotatedBug', fields ['url']
        db.delete_unique('bugsets_annotatedbug', ['url'])

        # Deleting model 'Skill'
        db.delete_table('bugsets_skill')

        # Removing M2M table for field bugs on 'BugSet'
        db.delete_table('bugsets_bugset_bugs')

        # Deleting field 'AnnotatedBug.title'
        db.delete_column('bugsets_annotatedbug', 'title')

        # Deleting field 'AnnotatedBug.description'
        db.delete_column('bugsets_annotatedbug', 'description')

        # Deleting field 'AnnotatedBug.assigned_to'
        db.delete_column('bugsets_annotatedbug', 'assigned_to')

        # Deleting field 'AnnotatedBug.mentor'
        db.delete_column('bugsets_annotatedbug', 'mentor')

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

        # Removing M2M table for field skills on 'AnnotatedBug'
        db.delete_table('bugsets_annotatedbug_skills')


    models = {
        'bugsets.annotatedbug': {
            'Meta': {'object_name': 'AnnotatedBug'},
            'assigned_to': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mentor': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'skills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bugsets.Skill']", 'symmetrical': 'False'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'u'", 'max_length': '1'}),
            'time_estimate': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'})
        },
        'bugsets.bugset': {
            'Meta': {'object_name': 'BugSet'},
            'bugs': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bugsets.AnnotatedBug']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'bugsets.skill': {
            'Meta': {'object_name': 'Skill'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        }
    }

    complete_apps = ['bugsets']
