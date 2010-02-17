
from south.db import db
from django.db import models
from mysite.search.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'ProjectInvolvementQuestion.key_string'
        db.add_column('search_projectinvolvementquestion', 'key_string', orm['search.projectinvolvementquestion:key_string'])
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'ProjectInvolvementQuestion.key_string'
        db.delete_column('search_projectinvolvementquestion', 'key_string')
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
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
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'search.answer': {
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'answers'", 'to': "orm['search.ProjectInvolvementQuestion']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'search.bug': {
            'bize_size_tag_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'canonical_bug_link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'concerns_just_documentation': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'date_reported': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'good_for_newcomers': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'importance': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'last_polled': ('django.db.models.fields.DateTimeField', [], {}),
            'last_touched': ('django.db.models.fields.DateTimeField', [], {}),
            'looks_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'people_involved': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'submitter_realname': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'submitter_username': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'search.buganswer': {
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'details': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['search.Project']"}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bug_answers'", 'to': "orm['search.ProjectInvolvementQuestion']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'search.hitcountcache': {
            'hashed_query': ('django.db.models.fields.CharField', [], {'max_length': '40', 'primary_key': 'True'}),
            'hit_count': ('django.db.models.fields.IntegerField', [], {})
        },
        'search.project': {
            'cached_contributor_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'date_icon_was_fetched_from_ohloh': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'icon_for_profile': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_for_search_result': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_raw': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_smaller_for_badge': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'icon_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'logo_contains_name': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        'search.projectinvolvementquestion': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_bug_style': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'key_string': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'text': ('django.db.models.fields.TextField', [], {})
        }
    }
    
    complete_apps = ['search']
