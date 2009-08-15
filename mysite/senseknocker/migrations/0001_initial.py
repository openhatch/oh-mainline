
from south.db import db
from django.db import models
from mysite.senseknocker.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Bug'
        db.create_table('senseknocker_bug', (
            ('id', orm['senseknocker.Bug:id']),
            ('background', orm['senseknocker.Bug:background']),
            ('expected_behavior', orm['senseknocker.Bug:expected_behavior']),
            ('actual_behavior', orm['senseknocker.Bug:actual_behavior']),
        ))
        db.send_create_signal('senseknocker', ['Bug'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Bug'
        db.delete_table('senseknocker_bug')
        
    
    
    models = {
        'senseknocker.bug': {
            'actual_behavior': ('django.db.models.fields.TextField', [], {}),
            'background': ('django.db.models.fields.TextField', [], {}),
            'expected_behavior': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }
    
    complete_apps = ['senseknocker']
