from django.conf.urls.defaults import *

from django.conf import settings

import django_authopenid
from django.contrib import admin
admin.autodiscover()

import mysite.account.forms

from django_authopenid import views as oid_views

urlpatterns = patterns('',
        # Invitation-related URLs
        (r'^invitation/', include('invitation.urls')),

        # FIXME: Automatically remove trailing slashes from input URLs,
        # and remove trailing slashes from the urls below.
        (r'^$', 'mysite.base.views.homepage'),
        (r'^search/$', 'mysite.search.views.fetch_bugs'),
        (r'^admin/(.*)', admin.site.root),
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),

        (r'^people/$', 'mysite.profile.views.display_list_of_people'),

        (r'^account/login/$', 'mysite.account.views.login'),
        (r'^account/forgot_pass/$', 'django.contrib.auth.views.password_reset', {'template_name': 'account/password_reset.html',
                                                                                 'email_template_name': 'account/password_reset_email.html'}),

        (r'^account/catch-me$', 'mysite.account.views.catch_me'),
        (r'^account/logout/$', 'mysite.account.views.logout'),

        (r'^account/login/do$', 'mysite.account.views.login_do'),
        (r'^account/signup/do$', 'mysite.account.views.signup_do'),

        (r'^account/request_invitation/do$',
            'mysite.account.views.request_invitation'),

        #Karen messes around with templates
        (r'^about/$', 
            'mysite.info.views.aboutpage'),
        (r'^contact/$', 
            'mysite.info.views.contactpage'),
        (r'^jobs/$', 
            'mysite.consulting.views.search'),
        (r'^jobs/(?P<query>.*)/$',
            'mysite.consulting.views.list'),
        (r'^people/(?P<user_to_display__username>[^/]+)/widget/$',
                'mysite.profile.views.widget_display'),

        (r'^people/(?P<user_to_display__username>[^/]+)/openhatch-widget.js$',
                'mysite.profile.views.widget_display_js'),

        (r'^people/info/edit/do$',
            'mysite.profile.views.edit_person_info'),

        (r'^people/project_icon/(?P<project_name>.*)$',
            'mysite.profile.views.project_icon_web'),

        (r'^people/project_icon_badge/(?P<project_name>.*)$',
            'mysite.profile.views.project_icon_web',
         {'width': 40}),

        # OpenID URL prefix for django_authopenid.urls
        url(r'^openid/signin/$', oid_views.signin, name='user_signin'),

        # OpenID URL prefix for django_authopenid.urls
        url(r'^openid/register/$', oid_views.register,
            kwargs=dict(register_form=mysite.account.forms.OpenidRegisterFormWithInviteCode)),

        # OpenID URL prefix for django_authopenid.urls
        url(r'^openid/register/$', oid_views.register, dict(send_email=False),
            name='user_register'),

        (r'^openid/', include('django_authopenid.urls')),
                       
        url(r'^account/forgot_pass_confirm/(?P<uidb36>[^/]+)/(?P<token>[^/]+)/$', 'django.contrib.auth.views.password_reset_confirm', {'template_name': 'account/password_reset_confirm.html', 'post_reset_redirect': '/account/forgot_pass_complete/'}, name='password_reset_confirm'),

        (r'^account/forgot_pass_done/', 'django.contrib.auth.views.password_reset_done', {'template_name': 'account/password_reset_done.html'}),

        (r'^account/forgot_pass_complete/', 'django.contrib.auth.views.password_reset_complete', {'template_name': 'account/password_reset_complete.html'}),

        url(r'^account/forgot_pass_confirm/(?P<uidb36>[^/]+)/(?P<token>[^/]+)/$', 'django.contrib.auth.views.password_reset_confirm', {'template_name': 'account/password_reset_confirm.html'}, name='password_reset_confirm'),

        (r'^account/signup/(?P<invite_code>[^/]+)?$',
           'mysite.account.views.signup'),

        (r'^account/settings/$',
            'mysite.account.views.settings'),

        (r'^account/settings/password/$',
            'mysite.account.views.change_password'),

        (r'^account/settings/invite_someone/$',
            'mysite.account.views.invite_someone'),

        (r'^account/settings/invite_someone/do$',
            'mysite.account.views.invite_someone_do'),

        (r'^account/settings/password/change$',
            'mysite.account.views.change_password_do'),

        (r'^account/settings/contact-info/$',
            'mysite.account.views.edit_contact_info'),

        (r'^account/settings/contact-info/do$',
            'mysite.account.views.edit_contact_info_do'),

        (r'^account/settings/widget/$',
                'mysite.account.views.widget'),

        (r'^account/edit/photo/$',
            'mysite.account.views.edit_photo'),

        (r'^account/edit/photo/do$',
            'mysite.account.views.edit_photo_do'),

        (r'^form/projectexp_add$',
            'mysite.profile.views.projectexp_add_form'),

        (r'^do/projectexp_add$',
            'mysite.profile.views.projectexp_add_do'),

        (r'^profile/views/add_citation_manually_do$',
            'mysite.profile.views.add_citation_manually_do'),

        # Get a list of suggestions for the search input,
        # formatted the way that the jQuery autocomplete plugin wants it.
        (r'^search/get_suggestions$', 'mysite.search.views.request_jquery_autocompletion_suggestions'),

        (r'^profile/views/gimme_json_for_portfolio$',
            'mysite.profile.views.gimme_json_for_portfolio'),

        (r'^profile/views/publish_citation_do$',
                'mysite.profile.views.publish_citation_do'),

        (r'^profile/views/delete_citation_do$',
                'mysite.profile.views.delete_citation_do'),

        (r'^profile/views/delete_portfolio_entry_do$',
                'mysite.profile.views.delete_portfolio_entry_do'),

        (r'^people/import/do$',
            'mysite.profile.views.import_do'),

        (r'^people/(?P<user_to_display__username>[^/]+)/projects/(?P<project__name>.+)$',
                'mysite.profile.views.projectexp_display'),

        (r'^people/projects/edit/(?P<project__name>.+)$',
                'mysite.profile.views.projectexp_edit'),

        (r'^people/projects/edit_do/(?P<project__name>.+)$',
                'mysite.profile.views.projectexp_edit_do'),

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

        (r'^test_404$', handler404),

        (r'^search/people/(?P<property>[^/]+)/(?P<value>.+)$',
                'mysite.profile.views.display_list_of_people_who_match_some_search'),

        # favicon.ico. Someday this should be handled by Apache.
        (r'^(favicon.ico)',
         'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT + '/images'}),

        # This dangerous regex is last
        (r'^people/(?P<user_to_display__username>[^/]+)[/?]$',
                'mysite.profile.views.display_person_web'),

        )

handler404 = 'mysite.base.views.page_not_found'

# vim: set ai ts=4 sts=4 et sw=4:
