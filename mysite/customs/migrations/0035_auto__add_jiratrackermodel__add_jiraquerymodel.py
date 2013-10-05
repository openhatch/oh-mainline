# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'JiraTrackerModel'
        db.create_table('customs_jiratrackermodel', (
            ('trackermodel_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['customs.TrackerModel'], unique=True, primary_key=True)),
            ('tracker_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('base_url', self.gf('django.db.models.fields.URLField')(unique=True, max_length=200)),
            ('bug_project_name_format', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('bitesized_type', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('bitesized_text', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
            ('documentation_text', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
        ))
        db.send_create_signal('customs', ['JiraTrackerModel'])

        # Adding model 'JiraQueryModel'
        db.create_table('customs_jiraquerymodel', (
            ('trackerquerymodel_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['customs.TrackerQueryModel'], unique=True, primary_key=True)),
            ('tracker', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['customs.JiraTrackerModel'])),
            ('state', self.gf('django.db.models.fields.CharField')(default='open', max_length=20)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=400)),
        ))
        db.send_create_signal('customs', ['JiraQueryModel'])


    def backwards(self, orm):

        # Deleting model 'JiraTrackerModel'
        db.delete_table('customs_jiratrackermodel')

        # Deleting model 'JiraQueryModel'
        db.delete_table('customs_jiraquerymodel')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
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
            'bitesized_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'bug_project_name_format': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'query_url_type': ('django.db.models.fields.CharField', [], {'default': "'xml'", 'max_length': '20'}),
            'tracker_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        'customs.githubquerymodel': {
            'Meta': {'object_name': 'GitHubQueryModel', '_ormbases': ['customs.TrackerQueryModel']},
            'state': ('django.db.models.fields.CharField', [], {'default': "'open'", 'max_length': '20'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.GitHubTrackerModel']"}),
            'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        'customs.githubtrackermodel': {
            'Meta': {'unique_together': "(('github_name', 'github_repo'),)", 'object_name': 'GitHubTrackerModel', '_ormbases': ['customs.TrackerModel']},
            'bitesized_tag': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'documentation_tag': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'github_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'github_repo': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
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
            'bitesized_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'google_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'tracker_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        'customs.jiraquerymodel': {
            'Meta': {'object_name': 'JiraQueryModel', '_ormbases': ['customs.TrackerQueryModel']},
            'state': ('django.db.models.fields.CharField', [], {'default': "'open'", 'max_length': '20'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.JiraTrackerModel']"}),
            'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '400'})
        },
        'customs.jiratrackermodel': {
            'Meta': {'object_name': 'JiraTrackerModel', '_ormbases': ['customs.TrackerModel']},
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'bitesized_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'bug_project_name_format': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'tracker_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        'customs.launchpadquerymodel': {
            'Meta': {'object_name': 'LaunchpadQueryModel', '_ormbases': ['customs.TrackerQueryModel']},
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.LaunchpadTrackerModel']"}),
            'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        'customs.launchpadtrackermodel': {
            'Meta': {'object_name': 'LaunchpadTrackerModel', '_ormbases': ['customs.TrackerModel']},
            'bitesized_tag': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'documentation_tag': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'launchpad_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
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
        'customs.roundupquerymodel': {
            'Meta': {'object_name': 'RoundupQueryModel', '_ormbases': ['customs.TrackerQueryModel']},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.RoundupTrackerModel']"}),
            'trackerquerymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerQueryModel']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '400'})
        },
        'customs.rounduptrackermodel': {
            'Meta': {'object_name': 'RoundupTrackerModel', '_ormbases': ['customs.TrackerModel']},
            'as_appears_in_distribution': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'bitesized_field': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'bitesized_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'closed_status': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'documentation_field': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'tracker_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'trackermodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['customs.TrackerModel']", 'unique': 'True', 'primary_key': 'True'})
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
            'created_for_project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']", 'null': 'True'}),
            'custom_parser': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
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
            'bitesized_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'bug_project_name_format': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'documentation_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
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
        },
        'profile.dataimportattempt': {
            'Meta': {'object_name': 'DataImportAttempt'},
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Person']"}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'web_response': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.WebResponse']", 'null': 'True'})
        },
        'profile.person': {
            'Meta': {'object_name': 'Person'},
            'bio': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'blacklisted_repository_committers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['profile.RepositoryCommitter']", 'symmetrical': 'False'}),
            'contact_blurb': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'dont_guess_my_location': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email_me_re_projects': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'expand_next_steps': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'gotten_name_from_ohloh': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'homepage_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'profile.repositorycommitter': {
            'Meta': {'unique_together': "(('project', 'data_import_attempt'),)", 'object_name': 'RepositoryCommitter'},
            'data_import_attempt': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.DataImportAttempt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"})
        },
        'search.project': {
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'logo_contains_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'people_who_wanna_help': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects_i_wanna_help'", 'symmetrical': 'False', 'to': "orm['profile.Person']"})
        }
    }

    complete_apps = ['customs']
