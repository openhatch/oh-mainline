#!/usr/bin/env python
from django_assets import Bundle, register
#http://elsdoerfer.name/docs/django-assets/bundles.html

register('openhatch_css',
         Bundle("css/base/base.css",
                "css/jquery.autocomplete.css",
                "css/jquery-ui-lightness/jquery-ui-1.7.2.custom.css",
                "openid/css/openid.css",
                "css/base/jquery.jgrowl.css",
                "css/senseknocker/thing.css",
                "css/search/search.css",
                "css/base/landing.css",
                "css/base/landing_page_for_logged_in_users.css",
                "css/profile/person_small.css",
                "css/project/project.css",
                "css/base/one_column.css",
                "css/base/two_columns.css",
                "css/base/three_columns.css",
                "css/account/auth.css",
                "css/account/settings.css",
                "css/account/widget.css",
                "css/qunit.css",
                "css/profile/base.css",
                "css/profile/portfolio.css",
                "css/profile/search_people.css",
                "css/tipsy.css",
                "css/facebox.css",
                "css/missions/base.css",
                "css/jquery-ui-lightness/jquery-ui-1.7.2.complete.css",
                ),
         output="packed/openhatch.css")
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
         # 1.7.2: core, sortable, progressbar, tabs
         Bundle('js/jquery-ui-1.7.2.custom.min.js',
                'js/jquery.tabs.js',
         	),
         #Bundle('jquery-ui/ui/jquery.ui.core.js',
         #       'jquery-ui/ui/jquery.ui.sortable.js',
         #       'jquery-ui/ui/jquery.ui.progressbar.js',
         #       'jquery-ui/ui/jquery.ui.tabs.js',
         #       ),
         
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

