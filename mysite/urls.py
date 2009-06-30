from django.conf.urls.defaults import *

import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
        (r'^$', 'mysite.search.views.fetch_bugs'),
        (r'^search/$', 'mysite.search.views.fetch_bugs'),
        (r'^admin/(.*)', admin.site.root),
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_DOC_ROOT}),
        (r'^people/$', 'mysite.profile.views.display_person_web'),
        (r'^people/get_data_for_email$', 'mysite.profile.views.get_data_for_email'),
        (r'^people/change_what_like_working_on$',
            'mysite.profile.views.change_what_like_working_on_web'),
        (r'^people/add_tag_to_project_exp$',
            'mysite.profile.views.add_tag_to_project_exp_web'),
        (r'^people/project_exp_tag__remove$',
            'mysite.profile.views.project_exp_tag__remove__web'),
        (r'^people/make_favorite_project_exp$',
            'mysite.profile.views.make_favorite_project_exp_web'),
        (r'^people/make_favorite_exp_tag$',
            'mysite.profile.views.make_favorite_exp_tag_web'),

        # Edit tags for an experience
        (r'^people/(?P<username>\w+)/edit-exp/tags/(?P<exp_id>\d+)$',
            'mysite.profile.views.edit_exp_tag'),

        # Edit a person's tags
        (r'^people/(?P<username>\w+)/tags/edit$',
            'mysite.profile.views.edit_person_tags'),

        # Check if Ohloh grab is done
        (r'^people/(?P<username>\w+)/ohloh_grab_done$',
            'mysite.profile.views.ohloh_grab_done_web'),

        # Project icons
        (r'^people/project_icon/(?P<project_name>.*)$',
            'mysite.profile.views.project_icon_web'),

        # Add contributions
        (r'^people/add_contrib$',
            'mysite.profile.views.display_person_old'),
        (r'^people/add_contribution$', 'mysite.profile.views.add_contribution_web'),

        (r'^people/(?P<username>\w+)/involvement/add/input$', 'mysite.profile.views.person_involvement_add_input'),
        (r'^people-actions/involvement/add$', 'mysite.profile.views.person_involvement_add'),

        # URL Raffi was writing for the bubble-closing page as he realized
        # we can't do this until we support authentication, la la la.
        #(r'^/people/%s/bubbles/%s/keep_closed[\.?]%s$' % (
        #    '(?P<username>\w_@-+)', '(?P<message_id>\w_-+)', '(?P<format>[a-z]+)'),
        #    'mysite.profile.views.bubble_keep_closed'),

        (r'^people/sf_projects_by_person$',
            'mysite.profile.views.sf_projects_by_person_web'),

        # Experience slurper
        (r'^people/xp_slurp$',
            'mysite.profile.views.xp_slurper_display_input_form'),
        (r'^people/xp_slurp_do$',
            'mysite.profile.views.exp_scraper_scrape_web'),
        (r'^people/show_all_data_for_person$',
            'mysite.profile.views.exp_scraper_display_for_person_web'),

        (r'^people/(?P<input_username>[^/]+)/import_contributions_image$',
            'mysite.profile.views.import_contributions_image'),

        # Get a list of suggestions for the search input, formatted the way that
        # the jQuery autocomplete plugin wants it.
        (r'^search/get_suggestions$', 'mysite.search.views.request_jquery_autocompletion_suggestions'),

        (r'^people/(?P<input_username>[^/]+)/test_commit_importer$',
            'mysite.profile.views.display_test_page_for_commit_importer'),

        (r'^people/(?P<input_username>[^/]+)/test_commit_importer_json$',
            'mysite.profile.views.get_commit_importer_json'),

        # Tabs
        (r'^people/(?P<input_username>[^/]+)/tabs?/(?P<tab>[a-z]+)[/?]$',
                'mysite.profile.views.display_person_web'),

        # This dangerous regex is last
        (r'^people/(?P<input_username>[^/]+)[/?]$',
                'mysite.profile.views.display_person_web'),


        )

# vim: set ai ts=4 sts=4 et sw=4:
