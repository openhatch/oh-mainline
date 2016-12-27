# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        for bqm in orm.BugzillaQueryModel.objects.all():
            bqm.query_type = bqm.tracker.query_url_type


    def backwards(self, orm):
        "Write your backwards methods here."
        pass


    models = {
        'customs.bugzillaquerymodel': {
            'Meta': {'object_name': 'BugzillaQueryModel', '_ormbases': ['customs.TrackerQueryModel']},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'query_type': ('django.db.models.fields.CharField', [], {'default': "'xml'", 'max_length': '20'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.BugzillaTrackerModel']"}),
            'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '400'})
        },
        'customs.bugzillatrackermodel': {
            'Meta': {'object_name': 'BugzillaTrackerModel', '_ormbases': ['customs.TrackerModel']},
            'as_appears_in_distribution': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10'}),
            'bug_project_name_format': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10'}),
            'query_url_type': ('django.db.models.fields.CharField', [], {'default': "'xml'", 'max_length': '20'}),
            'tracker_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        'customs.googlequerymodel': {
            'Meta': {'object_name': 'GoogleQueryModel', '_ormbases': ['customs.TrackerQueryModel']},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.GoogleTrackerModel']"}),
            'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        'customs.googletrackermodel': {
            'Meta': {'object_name': 'GoogleTrackerModel', '_ormbases': ['customs.TrackerModel']},
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10'}),
            'google_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'tracker_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
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
        'customs.trackermodel': {
            'Meta': {'object_name': 'TrackerModel'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_connections': ('django.db.models.fields.IntegerField', [], {'default': '8', 'blank': 'True'})
        },
        'customs.trackerquerymodel': {
            'Meta': {'object_name': 'TrackerQueryModel'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_polled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'})
        },
        'customs.tracquerymodel': {
            'Meta': {'object_name': 'TracQueryModel', '_ormbases': ['customs.TrackerQueryModel']},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.TracTrackerModel']"}),
            'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '400'})
        },
        'customs.tractimeline': {
            'Meta': {'object_name': 'TracTimeline'},
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_polled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'})
        },
        'customs.tractrackermodel': {
            'Meta': {'object_name': 'TracTrackerModel', '_ormbases': ['customs.TrackerModel']},
            'as_appears_in_distribution': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10'}),
            'bug_project_name_format': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '10', 'null': 'True'}),
            'old_trac': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tracker_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
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
