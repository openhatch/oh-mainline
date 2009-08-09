from mysite.base.views import view

@view
def form(request):
    return (request, "senseknocker/form.html", {})

# vim: ai ts=3 sts=4 et sw=4 nu
