# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Renaming field 'BugzillaTracker.project_name'
        db.rename_column('customs_bugzillatracker', 'project_name', 'tracker_name')

        # Renaming field 'GoogleTracker.project_name'
        db.rename_column('customs_googletracker', 'project_name', 'tracker_name')


    def backwards(self, orm):

        # Renaming field 'BugzillaTracker.tracker_name'
        db.rename_column('customs_bugzillatracker', 'tracker_name', 'project_name')

        # Renaming field 'GoogleTracker.tracker_name'
        db.rename_column('customs_googletracker', 'tracker_name', 'project_name')


    models = {
        'customs.bugzillatracker': {
            'Meta': {'object_name': 'BugzillaTracker'},
            'as_appears_in_distribution': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10'}),
            'bug_project_name_format': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'query_url_type': ('django.db.models.fields.CharField', [], {'default': "'xml'", 'max_length': '20'}),
            'tracker_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        'customs.bugzillaurl': {
            'Meta': {'object_name': 'BugzillaUrl'},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.BugzillaTracker']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '400'})
        },
        'customs.googlequery': {
            'Meta': {'object_name': 'GoogleQuery'},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.GoogleTracker']"})
        },
        'customs.googletracker': {
            'Meta': {'object_name': 'GoogleTracker'},
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10'}),
            'google_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tracker_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        'customs.recentmessagefromcia': {
            'Meta': {'object_name': 'RecentMessageFromCIA'},
            'branch': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'committer_identifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'module': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'project_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'time_received': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'customs.tracbugtimes': {
            'Meta': {'object_name': 'TracBugTimes'},
            'canonical_bug_link': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'date_reported': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_touched': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'latest_timeline_status': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '15', 'blank': 'True'}),
            'timeline': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.TracTimeline']"})
        },
        'customs.tractimeline': {
            'Meta': {'object_name': 'TracTimeline'},
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_polled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'})
        },
        'customs.webresponse': {
            'Meta': {'object_name': 'WebResponse'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response_headers': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['customs']
