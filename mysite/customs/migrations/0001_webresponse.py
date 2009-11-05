
from south.db import db
from django.db import models
from mysite.customs.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'WebResponse'
        db.create_table('customs_webresponse', (
            ('id', orm['customs.WebResponse:id']),
            ('text', orm['customs.WebResponse:text']),
            ('url', orm['customs.WebResponse:url']),
            ('status', orm['customs.WebResponse:status']),
            ('response_headers', orm['customs.WebResponse:response_headers']),
        ))
        db.send_create_signal('customs', ['WebResponse'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'WebResponse'
        db.delete_table('customs_webresponse')
        
    
    
    models = {
        'customs.webresponse': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response_headers': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.TextField', [], {})
        }
    }
    
    complete_apps = ['customs']
