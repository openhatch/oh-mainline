from django.http import HttpResponse, \
        HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response
import mysite.account
import mysite.account.forms
from django_authopenid.forms import OpenidSigninForm
from django.template import RequestContext, loader, Context
from django.core.urlresolvers import reverse
import mysite.profile as profile
from mysite.profile.views import display_person_web

def homepage(request, signup_form=None):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/people/%s' % request.user.username)

    form1 = OpenidSigninForm()

    signup_notification = login_notification = notification_id = None
    if request.GET.get('msg', None) == 'ciao':
        login_notification = "You've been logged out. Thanks for dropping in!"
        notification_id = 'ciao'
    # FIXME: I think the control block below is dead.
    elif request.GET.get('msg', None) == 'username_taken':
        signup_notification = "Your chosen username is already taken. Try another one."
        notification_id = 'username_taken'

    if not signup_form:
        signup_form = mysite.account.forms.UserCreationFormWithEmail()

    return render_to_response('base/homepage.html', {
        'signup_form': signup_form,
        'notification_id': notification_id,
        'login_notification': login_notification,
        'signup_notification': signup_notification,
        'form1': form1,
        }, context_instance=RequestContext(request))



