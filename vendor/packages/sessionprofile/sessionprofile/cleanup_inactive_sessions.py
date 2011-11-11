'''
Created on Dec 14, 2009

@author: russn
'''
import datetime
from django.core.management.base import NoArgsCommand
from django.contrib.sessions.models import Session
from django.db import transaction

from sessionprofile.models import SessionProfile

class Command(NoArgsCommand):
    help = """
    This purges inactive sessions from both the django session table and the 
    sessionprofile table used by the django-phpBB single sign-on code. 
    """


    def handle_noargs(self, **options):
        '''
        This purges inactive sessions from both the django session table and the 
        sessionprofile table used by the django-phpBB single sign-on code. 
        '''
        current_time = datetime.datetime.now()
        
        # Delete the sessionprofile objects which correspond to an expired sessions
        SessionProfile.objects.filter(session__expire_date__lt=current_time).delete()
        
        # Delete the session objects which correspond to an expired sessions
        Session.objects.filter(expire_date__lt=current_time).delete()
        
        transaction.commit_unless_managed()
