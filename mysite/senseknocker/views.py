from mysite.base.views import view, gimme_json
from forms import BugForm

@view
def form(request):
    form = BugForm()
    return (request, "senseknocker/form.html", {'form': form})

@gimme_json
def handle_form(request):
    form = BugForm(request.POST)
    if form.is_valid():
        form.user = request.user
        form.save()
        success = 1
    else:
        success = 0
    data = [{'success': success}]
    return data

# vim: ai ts=3 sts=4 et sw=4 nu
