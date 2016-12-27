# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Request'
        db.create_table(u'httpproxy_request', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('method', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('port', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=80)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('querykey', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'httpproxy', ['Request'])

        # Adding unique constraint on 'Request', fields ['method', 'domain', 'port', 'path', 'querykey']
        db.create_unique(u'httpproxy_request', ['method', 'domain', 'port', 'path', 'querykey'])

        # Adding model 'RequestParameter'
        db.create_table(u'httpproxy_requestparameter', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='parameters', to=orm['httpproxy.Request'])),
            ('type', self.gf('django.db.models.fields.CharField')(default='G', max_length=1)),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=250, null=True, blank=True)),
        ))
        db.send_create_signal(u'httpproxy', ['RequestParameter'])

        # Adding model 'Response'
        db.create_table(u'httpproxy_response', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('request', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['httpproxy.Request'], unique=True)),
            ('status', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=200)),
            ('content_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('content', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'httpproxy', ['Response'])


    def backwards(self, orm):
        # Removing unique constraint on 'Request', fields ['method', 'domain', 'port', 'path', 'querykey']
        db.delete_unique(u'httpproxy_request', ['method', 'domain', 'port', 'path', 'querykey'])

        # Deleting model 'Request'
        db.delete_table(u'httpproxy_request')

        # Deleting model 'RequestParameter'
        db.delete_table(u'httpproxy_requestparameter')

        # Deleting model 'Response'
        db.delete_table(u'httpproxy_response')


    models = {
        u'httpproxy.request': {
            'Meta': {'unique_together': "(('method', 'domain', 'port', 'path', 'querykey'),)", 'object_name': 'Request'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'port': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '80'}),
            'querykey': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'httpproxy.requestparameter': {
            'Meta': {'ordering': "('order',)", 'object_name': 'RequestParameter'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'request': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'parameters'", 'to': u"orm['httpproxy.Request']"}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'G'", 'max_length': '1'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'})
        },
        u'httpproxy.response': {
            'Meta': {'object_name': 'Response'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'request': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['httpproxy.Request']", 'unique': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '200'})
        }
    }

    complete_apps = ['httpproxy']