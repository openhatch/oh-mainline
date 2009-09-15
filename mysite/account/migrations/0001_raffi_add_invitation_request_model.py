
from south.db import db
from django.db import models
from mysite.account.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'InvitationRequest'
        db.create_table('account_invitationrequest', (
            ('id', orm['account.InvitationRequest:id']),
            ('first_name', orm['account.InvitationRequest:first_name']),
            ('last_name', orm['account.InvitationRequest:last_name']),
            ('email', orm['account.InvitationRequest:email']),
        ))
        db.send_create_signal('account', ['InvitationRequest'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'InvitationRequest'
        db.delete_table('account_invitationrequest')
        
    
    
    models = {
        'account.invitationrequest': {
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }
    
    complete_apps = ['account']
