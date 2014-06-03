from django.shortcuts import render
from mysite.bugsets.models import BugSet

def list_index(request):
    bugsets = BugSet.objects.all()
    context = {
        'bugsets': bugsets,
    }
    return render(request, 'list_index.html', context)

def listview_index(request, pk):
    bugset = BugSet.objects.get(pk=pk)
    bugs = bugset.annotatedbug_set.all()
    context = {
        'bugset' : bugset,
        'bugs': bugs,
    }
    return render(request, 'listview_index.html', context)
