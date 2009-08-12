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

def homepage(request, signup_form=None):
    if request.user.is_authenticated():
        return landing_page(request)

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

    invitation_request_form = mysite.account.forms.InvitationRequestForm()

    return render_to_response('base/homepage.html', {
        'notification_id': notification_id,
        'login_notification': login_notification,
        'signup_notification': signup_notification,
        'form1': form1,
        'signup_form': signup_form,
        'invitation_request_form': invitation_request_form,
        }, context_instance=RequestContext(request))

def landing_page(request):
    data = profile.views.get_personal_data(request.user.get_profile())
    data['the_user'] = request.user
    return render_to_response('base/landing.html', data)

def page_to_js(request):
    # FIXME: In the future, use:
    # from django.template.loader import render_to_string
    # to generate html_doc
    html_doc = "<strong>zomg</strong>"
    encoded_for_js = simplejson.dumps(html_doc)
    # Note: using application/javascript as suggested by
    # http://www.ietf.org/rfc/rfc4329.txt
    return render_to_response('base/append_ourselves.js',
                              {'in_string': encoded_for_js},
                              mimetype='application/javascript')
