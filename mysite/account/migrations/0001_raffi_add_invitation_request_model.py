# This file is part of OpenHatch.
# Copyright (C) 2009 OpenHatch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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
