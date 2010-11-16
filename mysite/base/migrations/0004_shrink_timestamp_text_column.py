
from south.db import db
from django.db import models
from mysite.base.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Changing field 'Timestamp.key'
        # (to signature: django.db.models.fields.CharField(unique=True, max_length=64))
        db.alter_column('base_timestamp', 'key', orm['base.timestamp:key'])
        
    
    
    def backwards(self, orm):
        
        # Changing field 'Timestamp.key'
        # (to signature: django.db.models.fields.CharField(max_length=255, unique=True))
        db.alter_column('base_timestamp', 'key', orm['base.timestamp:key'])
        
    
    
    models = {
        'base.timestamp': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        }
    }
    
    complete_apps = ['base']
