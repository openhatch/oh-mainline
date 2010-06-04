
from south.db import db
from django.db import models
from mysite.base.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Timestamp'
        db.create_table('base_timestamp', (
            ('id', orm['base.Timestamp:id']),
            ('key', orm['base.Timestamp:key']),
            ('timestamp', orm['base.Timestamp:timestamp']),
        ))
        db.send_create_signal('base', ['Timestamp'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Timestamp'
        db.delete_table('base_timestamp')
        
    
    
    models = {
        'base.timestamp': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['base']
