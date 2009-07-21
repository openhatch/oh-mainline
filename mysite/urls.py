from django.conf.urls.defaults import *

import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
        # FIXME: Automatically remove trailing slashes from input URLs,
        # and remove trailing slashes from the urls below.
        (r'^$', 'mysite.search.views.index'),
        (r'^search/$', 'mysite.search.views.fetch_bugs'),
        (r'^admin/(.*)', admin.site.root),
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_DOC_ROOT}),
        (r'^people/$', 'mysite.profile.views.display_list_of_people'),

        (r'^people/login/$', 'mysite.profile.views.login'),
        (r'^people/login/do$', 'mysite.profile.views.login_do'),
        (r'^people/logout/$', 'mysite.profile.views.logout'),
        (r'^people/signup/$', 'mysite.profile.views.signup'),
        (r'^people/signup/do$', 'mysite.profile.views.signup_do'),

        # FIXME: Either this or signup_do is dead code.
        (r'^people/new/do$', 'mysite.profile.views.new_user_do'),

        (r'^people/delete-experience/do$',
         'mysite.profile.views.delete_experience_do'),

        # FIXME: Add trailing slashes, as this is more permissive.
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
            'mysite.profile.views.ask_for_tag_input'),
        (r'^people/tags/edit/do$',
            'mysite.profile.views.edit_person_tags'),

        # Project icons
        (r'^people/project_icon/(?P<project_name>.*)$',
            'mysite.profile.views.project_icon_web'),

        # Add contributions
        (r'^people/add_contrib$',
            'mysite.profile.views.display_person_old'),
        (r'^people/add_contribution$', 'mysite.profile.views.add_contribution_web'),

        (r'^form/projectexp_add$', 'mysite.profile.views.projectexp_add_form'),
        (r'^do/projectexp_add$', 'mysite.profile.views.projectexp_add_do'),

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

        # Get a list of suggestions for the search input, formatted the way that
        # the jQuery autocomplete plugin wants it.
        (r'^search/get_suggestions$', 'mysite.search.views.request_jquery_autocompletion_suggestions'),

        (r'^people/test_commit_importer$',
            'mysite.profile.views.display_test_page_for_commit_importer'),

        (r'^people/test_commit_importer_json$',
            'mysite.profile.views.gimme_json_that_says_that_commit_importer_is_done'),

        (r'^people/import/do$',
            'mysite.profile.views.import_do'),

        # Tabs
        (r'^people/(?P<input_username>[^/]+)/tabs?/(?P<tab>[a-z]+)[/?]$',
                'mysite.profile.views.display_person_web'),

        (r'^people/(?P<user_to_display__username>[^/]+)/projects/(?P<project__name>[a-zA-Z -]+)[/?]$',
                'mysite.profile.views.projectexp_display'),

        (r'^people/projects/edit/(?P<project__name>[a-zA-Z -]+)[/?]$',
                'mysite.profile.views.projectexp_edit'),

        (r'^people/edit[/?]$',
                'mysite.profile.views.display_person_edit_web'),

        # This dangerous regex is last
        (r'^people/(?P<user_to_display__username>[^/]+)[/?]$',
                'mysite.profile.views.display_person_web'),

        )

# vim: set ai ts=4 sts=4 et sw=4:
