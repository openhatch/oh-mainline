import django_assets 

# Django Assets <http://github.com/miracle2k/django-assets>
# helps us bundle our assets, i.e., JavaScript and CSS,
# so they load faster.

# So django_assets doesn't feel bad creating files
ASSETS_AUTO_CREATE=True

# See documentation at <http://elsdoerfer.name/docs/django-assets/settings.html#assets-expire>
ASSETS_EXPIRE='filename'

# Bundle all of our JavaScripts into what Cal Henderson calls a "monolith".
# (See <http://carsonified.com/blog/dev/serving-javascript-fast/>.)
js_monolith = django_assets.Bundle(

        # JavaScripts kindly provided by other folks
        'static/js/jquery.js',
        'static/js/jquery.query.js',
        'static/js/jquery.json.js',
        'static/js/jquery.hint.js',
        'static/js/jquery.form.js',
        'static/js/jquery.jgrowl.js',
        'static/js/jquery-ui-1.7.2.custom.min.js',
        'static/js/jquery.cookie.js',
        'static/js/piwik.js',

        # Stuff we wrote
        'static/js/base/locationDialog.js',
        'static/js/base/base.js',
        'static/js/search/defaultText.js',
        'static/js/account/set_location.js',
        'static/js/profile/portfolio.js',
        'static/js/importer.js',  # ~32KB at time of writing (commit 391939b7)
        #'static/js/css_if_js.js', # I don't think we need this

        filters='jsmin',
        output='static/js/bundle.js')

django_assets.register('big_bundle_of_javascripts', js_monolith)
