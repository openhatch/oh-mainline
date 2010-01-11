import django_assets 

# Django Assets <http://github.com/miracle2k/django-assets>
# helps us bundle our assets, i.e., JavaScript and CSS,
# so they load faster.

# So django_assets doesn't feel bad creating files
ASSETS_AUTO_CREATE=True

# See documentation at <http://elsdoerfer.name/docs/django-assets/settings.html#assets-expire>
ASSETS_EXPIRE='filename'

# Below, we bundle all of our JavaScripts into what Cal Henderson calls a "monolith".
# (See <http://carsonified.com/blog/dev/serving-javascript-fast/>.)

# NB: "Note that...all filenames and paths are considered to be
# relative to Django’s MEDIA_ROOT settings, and generated urls will be based on MEDIA_URL."
# <http://elsdoerfer.name/docs/django-assets/bundles.html>

js_monolith = django_assets.Bundle(

        # JavaScripts kindly provided by other folks
#        'js/jquery.js',
        
#        'js/jquery.query.js',
#        'js/jquery.json.js',
#        'js/jquery.hint.js',
#        'js/jquery.form.js',
#        'js/jquery.jgrowl.js',
#        'js/jquery-ui-1.7.2.custom.min.js',
#        'js/jquery.cookie.js',
#        'js/piwik.js',
#
#        # Stuff we wrote
#        'js/base/locationDialog.js',
#        'js/base/base.js',
#        'js/search/defaultText.js',
#        'js/account/set_location.js',
#        'js/profile/portfolio.js',
#        'js/importer.js',  # ~32KB at time of writing (commit 391939b7)
        #'js/css_if_js.js', # I don't think we need this

        #filters='jsmin',
        output='bundle.js')

django_assets.register('big_bundle_of_javascripts', js_monolith)
