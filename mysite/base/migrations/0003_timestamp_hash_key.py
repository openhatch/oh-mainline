
from south.db import db
from django.db import models
from mysite.base.models import *

class Migration:
    no_dry_run = True
    
    def forwards(self, orm):
        "Write your forwards migration here"
        for timestamp in orm.Timestamp.objects.all():
            print 'Hashing', timestamp.key
            timestamp.key = Timestamp.hash(timestamp.key)
            timestamp.save()
    
    def backwards(self, orm):
        "Write your backwards migration here"
    
    
    models = {
        'base.timestamp': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        }
    }
    
    complete_apps = ['base']
