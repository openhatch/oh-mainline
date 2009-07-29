from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import render_to_response
import account.forms

def homepage(request, signup_form=None):
    signup_notification = login_notification = notification_id = None
    if request.GET.get('msg', None) == 'ciao':
        login_notification = "You've been logged out. Thanks for dropping in!"
        notification_id = 'ciao'
    elif request.GET.get('msg', None) == 'username_taken':
        signup_notification = "Your chosen username is already taken. Try another one."
        notification_id = 'username_taken'

    if not signup_form:
        signup_form = account.forms.UserCreationFormWithEmail()

    return render_to_response('base/homepage.html', {
        'title' : 'Welcome to OpenHatch', # FIXME: This doesn't work.
        'signup_form': signup_form,
        'notification_id': notification_id,
        'login_notification': login_notification,
        'signup_notification': signup_notification,
        })
