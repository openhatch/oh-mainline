
from south.db import db
from django.db import models
from mysite.profile.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'Forwarder.stops_being_listed_on'
        db.add_column('profile_forwarder', 'stops_being_listed_on', orm['profile.forwarder:stops_being_listed_on'])
        
        # Changing field 'DataImportAttempt.date_created'
        # (to signature: django.db.models.fields.DateTimeField(default=datetime.datetime(2010, 2, 26, 21, 30, 26, 783589)))
        db.alter_column('profile_dataimportattempt', 'date_created', orm['profile.dataimportattempt:date_created'])
        
        # Changing field 'PortfolioEntry.date_created'
        # (to signature: django.db.models.fields.DateTimeField(default=datetime.datetime(2010, 2, 26, 21, 30, 27, 433806)))
        db.alter_column('profile_portfolioentry', 'date_created', orm['profile.portfolioentry:date_created'])
        
        # Changing field 'Citation.date_created'
        # (to signature: django.db.models.fields.DateTimeField(default=datetime.datetime(2010, 2, 26, 21, 30, 27, 557269)))
        db.alter_column('profile_citation', 'date_created', orm['profile.citation:date_created'])
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'Forwarder.stops_being_listed_on'
        db.delete_column('profile_forwarder', 'stops_being_listed_on')
        
        # Changing field 'DataImportAttempt.date_created'
        # (to signature: django.db.models.fields.DateTimeField(default=datetime.datetime(2010, 2, 23, 16, 3, 21, 531657)))
        db.alter_column('profile_dataimportattempt', 'date_created', orm['profile.dataimportattempt:date_created'])
        
        # Changing field 'PortfolioEntry.date_created'
        # (to signature: django.db.models.fields.DateTimeField(default=datetime.datetime(2010, 2, 23, 16, 3, 21, 928244)))
        db.alter_column('profile_portfolioentry', 'date_created', orm['profile.portfolioentry:date_created'])
        
        # Changing field 'Citation.date_created'
        # (to signature: django.db.models.fields.DateTimeField(default=datetime.datetime(2010, 2, 23, 16, 3, 21, 746898)))
        db.alter_column('profile_citation', 'date_created', orm['profile.citation:date_created'])
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'customs.webresponse': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response_headers': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        'profile.citation': {
            'contributor_role': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'data_import_attempt': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.DataImportAttempt']", 'null': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2010, 2, 26, 21, 30, 28, 83393)'}),
            'distinct_months': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'first_commit_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignored_due_to_duplicate': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'languages': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'old_summary': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'portfolio_entry': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.PortfolioEntry']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'})
        },
        'profile.dataimportattempt': {
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2010, 2, 26, 21, 30, 29, 27056)'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Person']"}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'web_response': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customs.WebResponse']", 'null': 'True'})
        },
        'profile.forwarder': {
            'address': ('django.db.models.fields.TextField', [], {}),
            'expires_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stops_being_listed_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'profile.link_person_tag': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Person']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Tag']"})
        },
        'profile.link_project_tag': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Tag']"})
        },
        'profile.link_sf_proj_dude_fm': {
            'Meta': {'unique_together': "[('person', 'project')]"},
            'date_collected': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.SourceForgePerson']"}),
            'position': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.SourceForgeProject']"})
        },
        'profile.person': {
            'bio': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'blacklisted_repository_committers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['profile.RepositoryCommitter']"}),
            'contact_blurb': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'dont_guess_my_location': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'gotten_name_from_ohloh': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'homepage_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interested_in_working_on': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'last_polled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'location_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'location_display_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100'}),
            'photo_thumbnail': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100', 'null': 'True'}),
            'show_email': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'profile.portfolioentry': {
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2010, 2, 26, 21, 30, 27, 868361)'}),
            'experience_description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.Person']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'project_description': ('django.db.models.fields.TextField', [], {})
        },
        'profile.repositorycommitter': {
            'Meta': {'unique_together': "(('project', 'data_import_attempt'),)"},
            'data_import_attempt': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.DataImportAttempt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"})
        },
        'profile.sourceforgeperson': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'profile.sourceforgeproject': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'unixname': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'profile.tag': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profile.TagType']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'profile.tagtype': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'search.project': {
            'cached_contributor_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'date_icon_was_fetched_from_ohloh': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'icon_for_profile': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_for_search_result': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_raw': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_smaller_for_badge': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'logo_contains_name': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True'})
        }
    }
    
    complete_apps = ['profile']
