from mysite.base.decorators import view

@view
def main_page(request):
    return (request, 'missions/main.html', {})
