from decorator import decorator

@decorator
def view(func, *args, **kw):
    """Decorator for views."""
    request, template, view_data = func(*args, **kw)
    data = get_personal_data(request.user.get_profile())
    data['the_user'] = request.user
    data['slug'] = func.__name__
    data.update(view_data)
    return render_to_response(template, data)

