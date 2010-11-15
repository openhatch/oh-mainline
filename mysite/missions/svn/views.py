from mysite.missions.base.views import *
from mysite.missions.svn import forms, controllers

@login_required
def svn_resetrepo(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    controllers.SvnRepository(request.user.username).reset()
    controllers.unset_mission_completed(request.user.get_profile(), 'svn_checkout')
    controllers.unset_mission_completed(request.user.get_profile(), 'svn_diff')
    controllers.unset_mission_completed(request.user.get_profile(), 'svn_commit')
    if 'stay_on_this_page' in request.GET:
        return HttpResponseRedirect(reverse(svn_mission_about))
    else:
        return HttpResponseRedirect(reverse(svn_checkout))

def svn_data(request, passed_data={}):
    data = {
      'mission_name': 'Using Subversion',
      'svn_checkout_success': False,
      'svn_checkout_form': forms.SvnCheckoutForm(),
      'svn_checkout_error_message': '',
      'svn_diff_success': False,
      'svn_diff_form': forms.SvnDiffForm(),
      'svn_diff_error_message': '',
    }
    if request.user.is_authenticated():
        repo = controllers.SvnRepository(request.user.username)
        data.update({
            'repository_exists': repo.exists(),
            'svn_checkout_done': controllers.mission_completed(request.user.get_profile(), 'svn_checkout'),
            'svn_diff_done': controllers.mission_completed(request.user.get_profile(), 'svn_diff'),
            'svn_commit_done': controllers.mission_completed(request.user.get_profile(), 'svn_commit'),
        })
        if data['repository_exists']:
          data.update({
            'checkout_url': repo.public_trunk_url(),
            'secret_word_file': controllers.SvnCheckoutMission.SECRET_WORD_FILE,
            'file_for_svn_diff': controllers.SvnDiffMission.FILE_TO_BE_PATCHED,
            'new_secret_word': controllers.SvnCommitMission.NEW_SECRET_WORD,
            'commit_username': request.user.username,
            'commit_password': repo.get_password()
          })
    data.update(passed_data)
    return data

@view
def svn_mission_about(request, passed_data={}):
    data = svn_data(request, passed_data)
    data['this_mission_page_short_name'] = 'About'
    return (request, 'missions/svn/svn_about.html', data)

@login_required
@view
def svn_checkout(request, passed_data={}):
    data = svn_data(request, passed_data)
    data['this_mission_page_short_name'] = 'Checking out'
    return (request, 'missions/svn/svn_checkout.html', data)

@login_required
def svn_checkout_submit(request):
    data = {}
    if request.method == 'POST':
        form = forms.SvnCheckoutForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['secret_word'] == controllers.SvnCheckoutMission.get_secret_word(request.user.username):
                controllers.set_mission_completed(request.user.get_profile(), 'svn_checkout')
                return HttpResponseRedirect(reverse(svn_checkout))
            else:
                data['svn_checkout_error_message'] = 'The secret word is incorrect.'
        data['svn_checkout_form'] = form
    return svn_checkout(request, data)

@login_required
@view
def svn_diff(request, passed_data={}):
    data = svn_data(request, passed_data)
    data['this_mission_page_short_name'] = 'Diffing your changes'
    return (request, 'missions/svn/svn_diff.html', data)

@login_required
def svn_diff_submit(request):
    data = {}
    if request.method == 'POST':
        form = forms.SvnDiffForm(request.POST)
        if form.is_valid():
            try:
                controllers.SvnDiffMission.validate_diff_and_commit_if_ok(request.user.username, form.cleaned_data['diff'])
                controllers.set_mission_completed(request.user.get_profile(), 'svn_diff')
                return HttpResponseRedirect(reverse(svn_diff))
            except controllers.IncorrectPatch, e:
                data['svn_diff_error_message'] = str(e)
        data['svn_diff_form'] = form
    return svn_diff(request, data)

@login_required
@view
def svn_commit(request, passed_data={}):
    data = svn_data(request, passed_data)
    data['this_mission_page_short_name'] = 'Committing your changes'
    return (request, 'missions/svn/svn_commit.html', data)

@login_required
def svn_commit_poll(request):
    return HttpResponse(simplejson.dumps(controllers.mission_completed(request.user.get_profile(), 'svn_commit')))
