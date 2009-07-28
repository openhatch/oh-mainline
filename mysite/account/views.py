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
    username = request.POST.get('create_profile_username', None)
    password = request.POST.get('create_profile_password', None)
    if username and password:
        # create a user
        user, created = User.objects.get_or_create(username=username)
        if not created:
            # eep, redirect back to the front page with a message
            return HttpResponseRedirect('/?msg=username_taken#tab=create_profile')
        
        # Good, set the user's parameters.
        user.email=''
        user.set_password(password)
        user.save()
        
        # create a linked person
        person = Person(user=user)
        person.save()

        # authenticate and login
        user = django.contrib.auth.authenticate(
                username=username, password=password)
        django.contrib.auth.login(request, user)

        # redirect to profile
        return HttpResponseRedirect('/people/%s/' % urllib.quote(username))
    else:
        fail
        # FIXME: Validate, Catch no username
    # }}}

def logout(request):
    # {{{
    django.contrib.auth.logout(request)
    return HttpResponseRedirect("/?msg=ciao#tab=login")
    # }}}
