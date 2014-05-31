from django.shortcuts import render

def list_index(request):
    context = {}
    return render(request, 'list_index.html', context)
