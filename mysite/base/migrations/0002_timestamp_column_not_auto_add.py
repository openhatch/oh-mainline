
from south.db import db
from django.db import models
from mysite.base.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Changing field 'Timestamp.timestamp'
        # (to signature: django.db.models.fields.DateTimeField())
        db.alter_column('base_timestamp', 'timestamp', orm['base.timestamp:timestamp'])
        
    
    
    def backwards(self, orm):
        
        # Changing field 'Timestamp.timestamp'
        # (to signature: django.db.models.fields.DateTimeField(auto_now_add=True, blank=True))
        db.alter_column('base_timestamp', 'timestamp', orm['base.timestamp:timestamp'])
        
    
    
    models = {
        'base.timestamp': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        }
    }
    
    complete_apps = ['base']
