from django.conf.urls.defaults import *

import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
        # FIXME: Automatically remove trailing slashes from input URLs,
        # and remove trailing slashes from the urls below.
        (r'^$', 'mysite.base.views.homepage'),
        (r'^search/$', 'mysite.search.views.fetch_bugs'),
        (r'^admin/(.*)', admin.site.root),
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_DOC_ROOT}),
        (r'^people/$', 'mysite.profile.views.display_list_of_people'),

        (r'^account/login/$', 'mysite.account.views.login'),
        (r'^account/logout/$', 'mysite.account.views.logout'),

        (r'^account/login/do$', 'mysite.account.views.login_do'),
        (r'^account/signup/do$', 'mysite.account.views.signup_do'),

        #Karen messes around with templates
        (r'^jobs/$', 
            'mysite.consulting.views.search'),
        (r'^jobs/(?P<query>.*)/$',
            'mysite.consulting.views.list'),

        (r'^people/delete-experience/do$',
         'mysite.profile.views.delete_experience_do'),

        # FIXME: I think this is dead code and it causes problems when using
        # Django's %url% template tag.
        #(r'^people/project_exp_tag__remove$',
        #    'mysite.profile.views.project_exp_tag__remove__web'),

        (r'^people/info/edit/do$',
            'mysite.profile.views.edit_person_info'),

        (r'^people/project_icon/(?P<project_name>.*)$',
            'mysite.profile.views.project_icon_web'),

        (r'^account/edit/password/$',
            'mysite.account.views.edit_password'),

        (r'^account/edit/password/do$',
            'mysite.account.views.edit_password_do'),

        (r'^account/edit/photo/$',
            'mysite.account.views.edit_photo'),

        (r'^account/edit/photo/do$',
            'mysite.account.views.edit_photo_do'),

        (r'^account/edit/show-email/do$',
            'mysite.account.views.show_email_do'),

        (r'^form/projectexp_add$',
            'mysite.profile.views.projectexp_add_form'),

        (r'^do/projectexp_add$',
            'mysite.profile.views.projectexp_add_do'),

        # Get a list of suggestions for the search input,
        # formatted the way that the jQuery autocomplete plugin wants it.
        (r'^search/get_suggestions$', 'mysite.search.views.request_jquery_autocompletion_suggestions'),

        (r'^people/gimme_json_that_says_that_commit_importer_is_done$',
            'mysite.profile.views.gimme_json_that_says_that_commit_importer_is_done'),

        (r'^people/import/do$',
            'mysite.profile.views.import_do'),

        (r'^people/(?P<user_to_display__username>[^/]+)/projects/(?P<project__name>.+)$',
                'mysite.profile.views.projectexp_display'),

        (r'^people/projects/edit/(?P<project__name>.+)$',
                'mysite.profile.views.projectexp_edit'),

        (r'^people/portfolio/import/$',
                'mysite.profile.views.importer'),

        (r'^people/edit/info$',
                'mysite.profile.views.display_person_edit_web',
                { 'info_edit_mode': True }),

        (r'^edit/name$',
                'mysite.profile.views.display_person_edit_name',
                { 'name_edit_mode': True }),

        (r'^edit/name/do$',
                'mysite.profile.views.display_person_edit_name_do'),

        (r'^people/portfolio/import/prepare_data_import_attempts_do$',
                'mysite.profile.views.prepare_data_import_attempts_do'),

        (r'^people/user_selected_these_dia_checkboxes$',
                'mysite.profile.views.user_selected_these_dia_checkboxes'),

        # This dangerous regex is last
        (r'^people/(?P<user_to_display__username>[^/]+)[/?]$',
                'mysite.profile.views.display_person_web'),

        )

# vim: set ai ts=4 sts=4 et sw=4:
