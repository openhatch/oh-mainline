# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'Heard_From'
        db.create_table('profile_heard_from', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', unique=True, max_length=100)),
        ))
        db.send_create_signal('profile', ['Heard_From'])

        # Adding M2M table for field heard_from on 'Person'
        db.create_table('profile_person_heard_from', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('person', models.ForeignKey(orm['profile.person'], null=False)),
            ('heard_from', models.ForeignKey(orm['profile.heard_from'], null=False))
        ))
        db.create_unique('profile_person_heard_from', ['person_id', 'heard_from_id'])

        # Adding field 'Person.github_name'
        db.add_column('profile_person', 'github_name', self.gf('django.db.models.fields.CharField')(default='', max_length=100, blank=True), keep_default=False)

        # Adding field 'Person.google_code_name'
        db.add_column('profile_person', 'google_code_name', self.gf('django.db.models.fields.CharField')(default='', max_length=100, blank=True), keep_default=False)

        # Adding field 'Person.other_name'
        db.add_column('profile_person', 'other_name', self.gf('django.db.models.fields.CharField')(default='', max_length=100, blank=True), keep_default=False)

        # Adding field 'Person.comment'
        db.add_column('profile_person', 'comment', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

         # Adding field 'Person.comment'
        db.add_column('profile_person', 'language_spoken', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'Person.subscribed'
        db.add_column('profile_person', 'subscribed', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True), keep_default=False)

    def backwards(self, orm):

        # Deleting model 'Heard_From'
        db.delete_table('profile_heard_from')

        # Removing M2M table for field heard_from on 'Person'
        db.delete_table('profile_person_heard_from')

        # Deleting field 'Person.github_name'
        db.delete_column('profile_person', 'github_name')

        # Deleting field 'Person.google_code_name'
        db.delete_column('profile_person', 'google_code_name')

        # Deleting field 'Person.other_name'
        db.delete_column('profile_person', 'other_name')

        # Deleting field 'Person.comment'
        db.delete_column('profile_person', 'comment')

         # Deleting field 'Person.language_spoken'
        db.delete_column('profile_person', 'language_spoken')

        # Deleting field 'Person.subscribed'
        db.delete_column('profile_person', 'subscribed')

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
        'base.experience':{
        'Meta': {'object_name': 'Experience'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100'})
        },
        'base.organization': {
            'Meta': {'object_name': 'Organization'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100'})
        },
        'base.skill': {
            'Meta': {'object_name': 'Skill'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'customs.webresponse': {
            'Meta': {'object_name': 'WebResponse'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response_headers': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        'profile.cause': {
            'Meta': {'object_name': 'Cause'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100'})
        },
        'profile.citation': {
            'Meta': {'object_name': 'Citation'},
            'contributor_role': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'data_import_attempt': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.DataImportAttempt']", 'null': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'distinct_months': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'first_commit_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignored_due_to_duplicate': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'languages': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'old_summary': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'portfolio_entry': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.PortfolioEntry']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'})
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
        'profile.forwarder': {
            'Meta': {'object_name': 'Forwarder'},
            'address': ('django.db.models.fields.TextField', [], {}),
            'expires_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stops_being_listed_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'profile.heard_from': {
            'Meta': {'object_name': 'Heard_From'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100'})
        },
        'profile.language': {
            'Meta': {'object_name': 'Language'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100'})
        },
        'profile.link_person_tag': {
            'Meta': {'object_name': 'Link_Person_Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Person']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Tag']"})
        },
        'profile.link_project_tag': {
            'Meta': {'object_name': 'Link_Project_Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Tag']"})
        },
        'profile.link_sf_proj_dude_fm': {
            'Meta': {'unique_together': "[('person', 'project')]", 'object_name': 'Link_SF_Proj_Dude_FM'},
            'date_collected': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.SourceForgePerson']"}),
            'position': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.SourceForgeProject']"})
        },
        'profile.person': {
            'Meta': {'object_name': 'Person'},
            'bio': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'blacklisted_repository_committers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['profile.RepositoryCommitter']", 'symmetrical': 'False'}),
            'cause': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['profile.Cause']", 'symmetrical': 'False'}),
            'comment': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '100'}),
            'company_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'contact_blurb': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'dont_guess_my_location': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email_me_re_projects': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'expand_next_steps': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'github_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '100'}),
            'google_code_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '100'}),
            'gotten_name_from_ohloh': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'heard_from': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['profile.Heard_From']", 'symmetrical': 'False'}),
            'homepage_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'irc_nick': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['profile.Language']", 'symmetrical': 'False'}),
            'language_spoken': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '100'}),
            'last_polled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'default': '-37.3049962'}),
            'linked_in_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'location_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'location_display_name': ('django.db.models.fields.CharField', [], {'default': "'Inaccessible Island'", 'max_length': '255', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'default': '-12.6790445'}),
            'opensource': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'organization': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['base.Organization']", 'symmetrical': 'False'}),
            'other_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '100'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100'}),
            'photo_thumbnail': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100', 'null': 'True'}),
            'photo_thumbnail_20px_wide': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100', 'null': 'True'}),
            'photo_thumbnail_30px_wide': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100', 'null': 'True'}),
            'show_email': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'subscribed': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'skill': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['base.Skill']", 'symmetrical': 'False'}),
            'time_to_commit': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'to': "orm['profile.TimeToCommit']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'profile.portfolioentry': {
            'Meta': {'ordering': "('-sort_order', '-id')", 'object_name': 'PortfolioEntry'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'experience_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Person']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'project_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'receive_maintainer_updates': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'use_my_description': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'profile.repositorycommitter': {
            'Meta': {'unique_together': "(('project', 'data_import_attempt'),)", 'object_name': 'RepositoryCommitter'},
            'data_import_attempt': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.DataImportAttempt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"})
        },
        'profile.sourceforgeperson': {
            'Meta': {'object_name': 'SourceForgePerson'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'profile.sourceforgeproject': {
            'Meta': {'object_name': 'SourceForgeProject'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'unixname': ('django.db.models.fields.CharField', [], {'max_length': '200'})
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
        },
        'profile.timetocommit': {
            'Meta': {'object_name': 'TimeToCommit', 'db_table': "'profile_time_to_commit'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100'})
        },
        'profile.unsubscribetoken': {
            'Meta': {'object_name': 'UnsubscribeToken'},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Person']"}),
            'string': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
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
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['base.Organization']"}),
            'people_who_wanna_help': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects_i_wanna_help'", 'symmetrical': 'False', 'to': "orm['profile.Person']"}),
            'skills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['base.Skill']", 'symmetrical': 'False'})
        }
    }

    complete_apps = ['profile']
