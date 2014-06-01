from django.shortcuts import render
from mysite.bugsets.models import BugSet

def list_index(request):
    bugsets = BugSet.objects.all()
    context = {
        'bugsets': bugsets,
    }
    return render(request, 'list_index.html', context)
