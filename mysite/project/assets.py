#!/usr/bin/env python
from django_assets import Bundle, register
#http://elsdoerfer.name/docs/django-assets/bundles.html

register('header_js',
         # jQuery
         Bundle('js/jquery-1.3.2.js',
         	),
         filter='jsmin',
         output='packed/header.js')

register('openhatch_js',
         # jQuery
         Bundle('js/jquery.json.js',
                'js/jquery.hint.js',
                'js/jquery.form.js',
                'js/jquery.jgrowl.js',
                'js/jquery.tipsy.js',
                'js/tipsy-onload.js', #not really jQuery
                'js/jquery.cookie.js',
                'js/facebox.js',
                ),
         # jQuery UI - TODO: import source, and each part individually
         Bundle('js/jquery-ui-1.7.2.custom.min.js',
                'js/jquery.tabs.js',
         	),
         # jQuery Tools
         Bundle('openid/js/openid-jquery.js',
                'js/facebox.js',
                ),
         # Other 3rd party
         Bundle('js/filedrop.js',
                'js/filedrop-onload.js', # OpenHatch specific
                ),
         # OpenHatch
         Bundle('js/base.js',
                'js/base/locationDialog.js',
                'js/importer.js',
                'js/account/set_location.js',
                'js/search/search.js',
                'js/profile/portfolio.js'
                ),
         filter='jsmin',
         output='packed/openhatch.js')

