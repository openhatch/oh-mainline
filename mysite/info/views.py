from django.http import HttpResponse, \
        HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response
import mysite.account
import mysite.account.forms
from django_authopenid.forms import OpenidSigninForm
import simplejson
from django.template import RequestContext, loader, Context
from django.core.urlresolvers import reverse
import mysite.profile as profile
from mysite.profile.views import display_person_web

def aboutpage(request, signup_form=None):
    if request.user.is_authenticated():
        return aboutpageauth(request)

    return render_to_response('info/about.html', {
        'signup_form': signup_form,
        'notification_id': notification_id,
        'login_notification': login_notification,
        'signup_notification': signup_notification,
        'form1': form1,
        }, context_instance=RequestContext(request))

def aboutpageauth(request):
    data = profile.views.get_personal_data(request.user.get_profile())
    data['the_user'] = request.user
    return render_to_response('info/about.html', data)
    

def contactpage (request,signup_form=None):
    if request.user.is_authenticated():
        return contactpageauth(request)
        
    return render_to_response('info/contact.html', {
        'signup_form': signup_form,
        'notification_id': notification_id,
        'login_notification': login_notification,
        'signup_notification': signup_notification,
        'form1': form1,
        }, context_instance=RequestContext(request))

def contactpageauth(request):
    data = profile.views.get_personal_data(request.user.get_profile())
    data['the_user'] = request.user
    return render_to_response('info/contact.html', data)