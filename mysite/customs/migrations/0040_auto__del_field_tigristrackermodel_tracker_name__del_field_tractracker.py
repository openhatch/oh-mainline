# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'TigrisTrackerModel.tracker_name'
        db.delete_column(u'customs_tigristrackermodel', 'tracker_name')

        # Deleting field 'TracTrackerModel.tracker_name'
        db.delete_column(u'customs_tractrackermodel', 'tracker_name')

        # Deleting field 'GoogleTrackerModel.tracker_name'
        db.delete_column(u'customs_googletrackermodel', 'tracker_name')

        # Deleting field 'RoundupTrackerModel.tracker_name'
        db.delete_column(u'customs_rounduptrackermodel', 'tracker_name')

        # Deleting field 'BugzillaTrackerModel.tracker_name'
        db.delete_column(u'customs_bugzillatrackermodel', 'tracker_name')

        # Deleting field 'GitHubTrackerModel.tracker_name'
        db.delete_column(u'customs_githubtrackermodel', 'tracker_name')

        # Deleting field 'LaunchpadTrackerModel.tracker_name'
        db.delete_column(u'customs_launchpadtrackermodel', 'tracker_name')

        # Deleting field 'JiraTrackerModel.tracker_name'
        db.delete_column(u'customs_jiratrackermodel', 'tracker_name')


    def backwards(self, orm):
        # Adding field 'TigrisTrackerModel.tracker_name'
        db.add_column(u'customs_tigristrackermodel', 'tracker_name',
                      self.gf('django.db.models.fields.CharField')(default=None, max_length=200, unique=True),
                      keep_default=False)

        # Adding field 'TracTrackerModel.tracker_name'
        db.add_column(u'customs_tractrackermodel', 'tracker_name',
                      self.gf('django.db.models.fields.CharField')(default=None, max_length=200, unique=True),
                      keep_default=False)

        # Adding field 'GoogleTrackerModel.tracker_name'
        db.add_column(u'customs_googletrackermodel', 'tracker_name',
                      self.gf('django.db.models.fields.CharField')(default=None, max_length=200, unique=True),
                      keep_default=False)

        # Adding field 'RoundupTrackerModel.tracker_name'
        db.add_column(u'customs_rounduptrackermodel', 'tracker_name',
                      self.gf('django.db.models.fields.CharField')(default=None, max_length=200, unique=True),
                      keep_default=False)

        # Adding field 'BugzillaTrackerModel.tracker_name'
        db.add_column(u'customs_bugzillatrackermodel', 'tracker_name',
                      self.gf('django.db.models.fields.CharField')(default=None, max_length=200, unique=True),
                      keep_default=False)

        # Adding field 'GitHubTrackerModel.tracker_name'
        db.add_column(u'customs_githubtrackermodel', 'tracker_name',
                      self.gf('django.db.models.fields.CharField')(default=None, max_length=200, unique=True),
                      keep_default=False)

        # Adding field 'LaunchpadTrackerModel.tracker_name'
        db.add_column(u'customs_launchpadtrackermodel', 'tracker_name',
                      self.gf('django.db.models.fields.CharField')(default=None, max_length=200, unique=True),
                      keep_default=False)

        # Adding field 'JiraTrackerModel.tracker_name'
        db.add_column(u'customs_jiratrackermodel', 'tracker_name',
                      self.gf('django.db.models.fields.CharField')(default=None, max_length=200, unique=True),
                      keep_default=False)


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'customs.bugzillaquerymodel': {
            'Meta': {'object_name': 'BugzillaQueryModel', '_ormbases': [u'customs.TrackerQueryModel']},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'query_type': ('django.db.models.fields.CharField', [], {'default': "'xml'", 'max_length': '20'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['customs.BugzillaTrackerModel']"}),
            u'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '400'})
        },
        u'customs.bugzillatrackermodel': {
            'Meta': {'object_name': 'BugzillaTrackerModel', '_ormbases': [u'customs.TrackerModel']},
            'as_appears_in_distribution': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'bug_project_name_format': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'query_url_type': ('django.db.models.fields.CharField', [], {'default': "'xml'", 'max_length': '20'}),
            u'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'customs.githubquerymodel': {
            'Meta': {'object_name': 'GitHubQueryModel', '_ormbases': [u'customs.TrackerQueryModel']},
            'state': ('django.db.models.fields.CharField', [], {'default': "'open'", 'max_length': '20'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['customs.GitHubTrackerModel']"}),
            u'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'customs.githubtrackermodel': {
            'Meta': {'unique_together': "(('github_name', 'github_repo'),)", 'object_name': 'GitHubTrackerModel', '_ormbases': [u'customs.TrackerModel']},
            'bitesized_tag': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'documentation_tag': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'github_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'github_repo': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'customs.googlequerymodel': {
            'Meta': {'object_name': 'GoogleQueryModel', '_ormbases': [u'customs.TrackerQueryModel']},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['customs.GoogleTrackerModel']"}),
            u'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'customs.googletrackermodel': {
            'Meta': {'object_name': 'GoogleTrackerModel', '_ormbases': [u'customs.TrackerModel']},
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'google_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            u'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'customs.jiraquerymodel': {
            'Meta': {'object_name': 'JiraQueryModel', '_ormbases': [u'customs.TrackerQueryModel']},
            'state': ('django.db.models.fields.CharField', [], {'default': "'open'", 'max_length': '20'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['customs.JiraTrackerModel']"}),
            u'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'customs.jiratrackermodel': {
            'Meta': {'object_name': 'JiraTrackerModel', '_ormbases': [u'customs.TrackerModel']},
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'bug_project_name_format': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            u'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'customs.launchpadquerymodel': {
            'Meta': {'object_name': 'LaunchpadQueryModel', '_ormbases': [u'customs.TrackerQueryModel']},
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['customs.LaunchpadTrackerModel']"}),
            u'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'customs.launchpadtrackermodel': {
            'Meta': {'object_name': 'LaunchpadTrackerModel', '_ormbases': [u'customs.TrackerModel']},
            'bitesized_tag': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'documentation_tag': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'launchpad_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            u'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'customs.roundupquerymodel': {
            'Meta': {'object_name': 'RoundupQueryModel', '_ormbases': [u'customs.TrackerQueryModel']},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['customs.RoundupTrackerModel']"}),
            u'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '400'})
        },
        u'customs.rounduptrackermodel': {
            'Meta': {'object_name': 'RoundupTrackerModel', '_ormbases': [u'customs.TrackerModel']},
            'as_appears_in_distribution': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'bitesized_field': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'closed_status': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'documentation_field': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            u'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'customs.tigrisquerymodel': {
            'Meta': {'object_name': 'TigrisQueryModel', '_ormbases': [u'customs.TrackerQueryModel']},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'startid': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['customs.TigrisTrackerModel']"}),
            u'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'customs.tigristrackermodel': {
            'Meta': {'object_name': 'TigrisTrackerModel', '_ormbases': [u'customs.TrackerModel']},
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            u'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'customs.tracbugtimes': {
            'Meta': {'object_name': 'TracBugTimes'},
            'canonical_bug_link': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'date_reported': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_touched': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'latest_timeline_status': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '15', 'blank': 'True'}),
            'timeline': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['customs.TracTimeline']"})
        },
        u'customs.trackermodel': {
            'Meta': {'object_name': 'TrackerModel'},
            'created_for_project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['search.Project']", 'null': 'True'}),
            'custom_parser': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_connections': ('django.db.models.fields.IntegerField', [], {'default': '8', 'blank': 'True'})
        },
        u'customs.trackerquerymodel': {
            'Meta': {'object_name': 'TrackerQueryModel'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_polled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'})
        },
        u'customs.tracquerymodel': {
            'Meta': {'object_name': 'TracQueryModel', '_ormbases': [u'customs.TrackerQueryModel']},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['customs.TracTrackerModel']"}),
            u'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '400'})
        },
        u'customs.tractimeline': {
            'Meta': {'object_name': 'TracTimeline'},
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_polled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'})
        },
        u'customs.tractrackermodel': {
            'Meta': {'object_name': 'TracTrackerModel', '_ormbases': [u'customs.TrackerModel']},
            'as_appears_in_distribution': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'bug_project_name_format': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'old_trac': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'customs.webresponse': {
            'Meta': {'object_name': 'WebResponse'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response_headers': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        u'profile.person': {
            'Meta': {'object_name': 'Person'},
            'bio': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'blacklisted_repository_committers': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['profile.RepositoryCommitter']", 'symmetrical': 'False'}),
            'contact_blurb': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'dont_guess_my_location': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email_me_re_projects': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'expand_next_steps': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'gotten_name_from_ohloh': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'homepage_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'irc_nick': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'last_polled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'default': '-37.3049962'}),
            'location_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'location_display_name': ('django.db.models.fields.CharField', [], {'default': "'Inaccessible Island'", 'max_length': '255', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'default': '-12.6790445'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100'}),
            'photo_thumbnail': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100', 'null': 'True'}),
            'photo_thumbnail_20px_wide': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100', 'null': 'True'}),
            'photo_thumbnail_30px_wide': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100', 'null': 'True'}),
            'show_email': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'profile.repositorycommitter': {
            'Meta': {'object_name': 'RepositoryCommitter'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['search.Project']"})
        },
        u'search.project': {
            'Meta': {'object_name': 'Project'},
            'cached_contributor_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'date_icon_was_fetched_from_ohloh': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'homepage': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'icon_for_profile': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_for_search_result': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_raw': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'icon_smaller_for_badge': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'logo_contains_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'people_who_wanna_help': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects_i_wanna_help'", 'symmetrical': 'False', 'to': u"orm['profile.Person']"})
        }
    }

    complete_apps = ['customs']