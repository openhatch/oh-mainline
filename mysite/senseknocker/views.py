from mysite.base.views import view, gimme_json

@view
def form(request):
    return (request, "senseknocker/form.html", {})

@gimme_json
def handle_form(request):
    # FIXME: Actually handle the form.
    data = [{'success': 1}]
    return data

# vim: ai ts=3 sts=4 et sw=4 nu
