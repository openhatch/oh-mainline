from mysite.base.decorators import view
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

@view
def main_page(request):
    return (request, 'missions/main.html', {})

@view
def diffpatch_info(request):
    return (request, 'missions/diffpatch_info.html', {})

def diffpatch_start(request):
    # TODO: mark mission as in progress
    return HttpResponseRedirect(reverse(diffpatch_progress))

@view
def diffpatch_progress(request):
    # TODO: make the mission actually do stuff
    return (request, 'missions/diffpatch_progress.html', {})
