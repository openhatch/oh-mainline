import mysite.base.decorators
import os
from django.http import Http404


@mysite.base.decorators.view
def show_checklist(request, slug):
    '''Get .step file, parse it, and send it to the template'''
    try:
        step_file = open(os.getcwd() + '/data/' + slug + '.step', 'r')
    except IOError:
        raise Http404

    return (request,
            'checklists/checklist.html',
            context)
