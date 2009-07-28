# Imports {{{
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from mysite.profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag, Link_Project_Tag, Link_SF_Proj_Dude_FM, Link_Person_Tag, DataImportAttempt
import django.contrib.auth 
from django.contrib.auth.models import User
import urllib
# }}}

def login(request):
    # {{{
    notification = notification_id = None
    if request.GET.get('msg', None) == 'oops':
        notification_id = "oops"
        notification = "Couldn't find that pair of username and password. "
        notification += "Did you type your password correctly?"
    if request.GET.get('next', None) is not None:
        notification_id = "next"
        notification = "You've got to be logged in to do that!"
    return render_to_response('account/login.html', {
        'notification_id': notification_id,
        'notification': notification,
        } )
    # }}}

def login_do(request):
    # {{{
    try:
        username = request.POST['login_username']
        password = request.POST['login_password']
    except KeyError:
        return HttpResponseServerError("Missing username or password.")
    user = django.contrib.auth.authenticate(
            username=username, password=password)
    if user is not None:
        django.contrib.auth.login(request, user)
        return HttpResponseRedirect('/people/%s' % urllib.quote(username))
    else:
        return HttpResponseRedirect('/account/login/?msg=oops')
    # }}}

def signup_do(request):
    # {{{
    # FIXME: Use Django form on homepage.
    form = UserCreationFormWithEmail(request.POST)
    if not form.errors:

        form.save()

        # create a linked person
        person = Person(user=user)
        person.save()

        # authenticate and login
        user = django.contrib.auth.authenticate(
                username=request.POST['username'],
                password=request.POST['password'])
        django.contrib.auth.login(request, user)

        # redirect to profile
        return HttpResponseRedirect(
                '/people/%s/' % urllib.quote(username))
    # }}}

def logout(request):
    # {{{
    django.contrib.auth.logout(request)
    return HttpResponseRedirect("/?msg=ciao#tab=login")
    # }}}
