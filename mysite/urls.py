from django.conf.urls.defaults import *
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import redirect

from django.conf import settings

import django_authopenid
from django.contrib import admin
admin.autodiscover()

import mysite.account.forms

from django_authopenid import views as oid_views

from voting.views import vote_on_object

import mysite.account.views

urlpatterns = patterns('',
        ### Okay, sometimes people link /, or /) because of bad linkification
        ### if so, just permit it as a redirect.
        (r'^,$', lambda x: HttpResponsePermanentRedirect('/')),
        (r'^\)$', lambda x: HttpResponsePermanentRedirect('/')),

        (r'^\+meta/', 'mysite.base.views.meta'),

        (r'^\+test_weekly_email_re_projects/', 'mysite.base.views.test_weekly_email_re_projects'),

        (r'^\+project_icon_poll/(?P<project_name>.+)', 'mysite.search.views.project_has_icon'),

        (r'^\+unsubscribe/(?P<token_string>.+)', 'mysite.profile.views.unsubscribe'),

        (r'^-profile.views.unsubscribe_do',
            'mysite.profile.views.unsubscribe_do'),

        (r'^\+projects/suggest_question/',
            'mysite.project.views.suggest_question'),

        (r'^\+projedit/(?P<project__name>.+)',
            'mysite.project.views.edit_project'),

        (r'^\+projects/suggest_question_do/',
            'mysite.project.views.suggest_question_do'),

        (r'^\+do/project.views.wanna_help_do',
            'mysite.project.views.wanna_help_do'),

        (r'^\+do/profile.views.set_expand_next_steps_do',
            'mysite.profile.views.set_expand_next_steps_do'),

        (r'^\+do/project.views.unlist_self_from_wanna_help_do',
            'mysite.project.views.unlist_self_from_wanna_help_do'),

        (r'^\+projects/create_project_page_do',
            'mysite.project.views.create_project_page_do'),
        # Generic view to vote on Link objects
        (r'^\+answer/vote/(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/?$',
            vote_on_object, dict(model=mysite.search.models.Answer,
                #template_object_name='answer',
                #template_name='kb/link_confirm_vote.html',
                allow_xmlhttprequest=True)),

        # Mission-related URLs
        (r'^missions/$', 'mysite.missions.views.main_page'),
        (r'^missions/tar$', 'mysite.missions.views.tar_mission_about'),
        (r'^missions/tar/unpacking$', 'mysite.missions.views.tar_mission_unpacking'),
        (r'^missions/tar/creating$', 'mysite.missions.views.tar_mission_creating'),
        (r'^missions/tar/hints$', 'mysite.missions.views.tar_mission_hints'),
        (r'^missions/tar/upload$', 'mysite.missions.views.tar_upload'),
        (r'^missions/tar/downloadfile/(?P<name>.*)', 'mysite.missions.views.tar_file_download'),
        (r'^missions/tar/downloadtarball', 'mysite.missions.views.tar_download_tarball_for_extract_mission'),
        (r'^missions/tar/extractupload', 'mysite.missions.views.tar_extract_mission_upload'),

        (r'^missions/diffpatch$', 'mysite.missions.views.diffpatch_mission_about'),
        (r'^missions/diffpatch/single_diff$', 'mysite.missions.views.diffpatch_mission_single_file_diff'),
        (r'^missions/diffpatch/single_patch$', 'mysite.missions.views.diffpatch_mission_single_file_patch'),
        (r'^missions/diffpatch/recursive_diff$', 'mysite.missions.views.diffpatch_mission_recursive_diff'),
        (r'^missions/diffpatch/recursive_patch$', 'mysite.missions.views.diffpatch_mission_recursive_patch'),
        (r'^missions/diffpatch/patchsingle/original$', 'mysite.missions.views.diffpatch_patchsingle_get_original_file'),
        (r'^missions/diffpatch/patchsingle/patch$', 'mysite.missions.views.diffpatch_patchsingle_get_patch'),
        (r'^missions/diffpatch/patchsingle/submit$', 'mysite.missions.views.diffpatch_patchsingle_submit'),
        (r'^missions/diffpatch/diffsingle/original$', 'mysite.missions.views.diffpatch_diffsingle_get_original_file'),
        (r'^missions/diffpatch/diffsingle/submit$', 'mysite.missions.views.diffpatch_diffsingle_submit'),
        (r'^missions/diffpatch/diffrecursive/original$', 'mysite.missions.views.diffpatch_diffrecursive_get_original_tarball'),
        (r'^missions/diffpatch/diffrecursive/submit$', 'mysite.missions.views.diffpatch_diffrecursive_submit'),
        (r'^missions/diffpatch/patchrecursive/original$', 'mysite.missions.views.diffpatch_patchrecursive_get_original_tarball'),
        (r'^missions/diffpatch/patchrecursive/patch$', 'mysite.missions.views.diffpatch_patchrecursive_get_patch'),
        (r'^missions/diffpatch/patchrecursive/submit$', 'mysite.missions.views.diffpatch_patchrecursive_submit'),

        (r'^missions/svn$', 'mysite.missions.views.svn_mission_about'),
        (r'^missions/svn/resetrepo$', 'mysite.missions.views.svn_resetrepo'),
        (r'^missions/svn/checkout$', 'mysite.missions.views.svn_checkout'),
        (r'^missions/svn/checkout/submit$', 'mysite.missions.views.svn_checkout_submit'),
        (r'^missions/svn/diff$', 'mysite.missions.views.svn_diff'),
        (r'^missions/svn/diff/submit$', 'mysite.missions.views.svn_diff_submit'),
        (r'^missions/svn/commit$', 'mysite.missions.views.svn_commit'),
        (r'^missions/svn/commit/poll$', 'mysite.missions.views.svn_commit_poll'),

        # Customs-related URLs
        (r'^customs/$', 'mysite.customs.views.list_trackers'),
        url(r'^customs/add$', 'mysite.customs.views.add_tracker', name='add_tracker_choose_type'),
        url(r'^customs/add/do$', 'mysite.customs.views.add_tracker_do', name='add_tracker_choose_type_do'),
        url(r'^customs/add/(?P<tracker_type>\w*)$', 'mysite.customs.views.add_tracker', name='add_tracker_specific'),
        url(r'^customs/add/(?P<tracker_type>\w*)/do$', 'mysite.customs.views.add_tracker_do', name='add_tracker_specific_do'),
        (r'^customs/add/(?P<tracker_type>\w*)/(?P<project_name>\w*)/url$', 'mysite.customs.views.add_tracker_url'),
        (r'^customs/add/(?P<tracker_type>\w*)/(?P<project_name>\w*)/url/do$', 'mysite.customs.views.add_tracker_url_do'),
        (r'^customs/edit/(?P<tracker_type>\w*)/(?P<project_name>\w*)$', 'mysite.customs.views.edit_tracker'),
        (r'^customs/edit/(?P<tracker_type>\w*)/(?P<project_name>\w*)/do$', 'mysite.customs.views.edit_tracker_do'),
        (r'^customs/edit/(?P<tracker_type>\w*)/(?P<project_name>\w*)/url$', 'mysite.customs.views.edit_tracker_url'),
        (r'^customs/edit/(?P<tracker_type>\w*)/(?P<project_name>\w*)/url/do$', 'mysite.customs.views.edit_tracker_url_do'),
        (r'^customs/delete/(?P<tracker_type>\w*)/(?P<project_name>\w*)$', 'mysite.customs.views.delete_tracker'),
        (r'^customs/delete/(?P<tracker_type>\w*)/(?P<project_name>\w*)/do$', 'mysite.customs.views.delete_tracker_do'),
        (r'^customs/delete/(?P<tracker_type>\w*)/(?P<project_name>\w*)/url$', 'mysite.customs.views.delete_tracker_url'),
        (r'^customs/delete/(?P<tracker_type>\w*)/(?P<project_name>\w*)/url/do$', 'mysite.customs.views.delete_tracker_url_do'),

        # Invitation-related URLs
        (r'^invitation/', include('invitation.urls')),

        (r'^$', 'mysite.base.views.home'),

        (r'^\+landing/import$', 'mysite.base.views.landing_for_documenters'),
        (r'^\+landing/opps$', 'mysite.base.views.landing_for_opp_hunters'),
        (r'^\+landing/projects$', 'mysite.base.views.landing_for_project_maintainers'),

        (r'^search/$', 'mysite.search.views.fetch_bugs'),
        (r'^admin/(.*)', admin.site.root),
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),

        (r'^people/$',
            'mysite.profile.views.people'),

        (r'^\+people/list/$', lambda x: HttpResponsePermanentRedirect('/people/')),

        (r'^account/forgot_pass/$',
            'django.contrib.auth.views.password_reset', {
                'template_name': 'account/password_reset.html',
                'email_template_name': 'account/password_reset_email.html'
                },
            "oh_forgot_pass"),

        (r'^account/catch-me$', 'mysite.account.views.catch_me'),

        (r'^account/login/$', 'django.contrib.auth.views.login', 
            {'template_name': 'account/login.html'},
            'oh_login'),
        (r'^account/login/do$', 'django.contrib.auth.views.login', 
            {'template_name': 'account/login.html'}),
        (r'^account/login/old$', 'django.contrib.auth.views.login', 
            {'template_name': 'account/login_old.html'},
            'oh_login_pwd'),

        (r'^account/logout/$', 'django.contrib.auth.views.logout',
            {
                #'next_page': '/',
                'redirect_field_name': 'next'
                },
            'oh_logout'),

        (r'^account/signup/do$', 'mysite.account.views.signup_do'),

        (r'^people/(?P<user_to_display__username>[^/]+)/widget/$',
                'mysite.profile.views.widget_display'),

        (r'^people/(?P<user_to_display__username>[^/]+)/openhatch-widget.js$',
                'mysite.profile.views.widget_display_js'),

        (r'^people/info/edit/do$',
            'mysite.profile.views.edit_person_info_do'),

        # OpenID URL prefix for django_authopenid.urls
        url(r'^openid/signin/$', oid_views.signin, name='user_signin'),

        # OpenID URL prefix for django_authopenid.urls
        url(r'^openid/register/$',
                mysite.account.views.register,
            name='user_register'),

        url(r'^openid/register/do$', 'mysite.account.views.register'),

        (r'^openid/', include('django_authopenid.urls')),
                       
        url(r'^account/forgot_pass_confirm/(?P<uidb36>[^/]+)/(?P<token>[^/]+)/$', 'django.contrib.auth.views.password_reset_confirm', {'template_name': 'account/password_reset_confirm.html', 'post_reset_redirect': '/account/forgot_pass_complete/'}, name='password_reset_confirm'),

        (r'^account/forgot_pass_done/', 'django.contrib.auth.views.password_reset_done', {'template_name': 'account/password_reset_done.html'}),

        (r'^account/forgot_pass_complete/', 'django.contrib.auth.views.password_reset_complete', {'template_name': 'account/password_reset_complete.html'}),

        url(r'^account/forgot_pass_confirm/(?P<uidb36>[^/]+)/(?P<token>[^/]+)/$', 'django.contrib.auth.views.password_reset_confirm', {'template_name': 'account/password_reset_confirm.html'}, name='password_reset_confirm'),

        url(r'\+do/save_portfolio_entry_ordering_do',
                'mysite.base.views.save_portfolio_entry_ordering_do'),

        url(r'\^do/profile.views.set_pfentries_dot_use_my_description_do',
                'mysite.profile.views.set_pfentries_dot_use_my_description_do'),

        (r'^account/signup/$',
           'mysite.account.views.signup'),

        (r'^account/settings/$',
            'mysite.account.views.settings'),

        (r'^account/settings/edit_name$',
            'mysite.account.views.edit_name'),

        (r'^account/settings/edit_name_do$',
            'mysite.account.views.edit_name_do'),

        (r'^account/settings/password/$',
            'mysite.account.views.change_password'),

        (r'^account/settings/location/$',
            'mysite.account.views.set_location'),

        (r'^account/settings/location/do$',
            'mysite.account.views.set_location_do'),

        (r'^account/settings/location/confirm_suggestion/do$',
            'mysite.account.views.confirm_location_suggestion_do'),

        (r'^account/settings/location/dont_guess_location/do$',
            'mysite.account.views.dont_guess_location_do'),

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

        (r'^profile/views/add_citation_manually_do$',
            'mysite.profile.views.add_citation_manually_do'),

        (r'^profile/views/replace_icon_with_default$',
            'mysite.profile.views.replace_icon_with_default'),

        # Get a list of suggestions for the search input,
        # formatted the way that the jQuery autocomplete plugin wants it.
        (r'^search/get_suggestions$', 'mysite.search.views.request_jquery_autocompletion_suggestions'),

        (r'^profile/views/gimme_json_for_portfolio$',
            'mysite.profile.views.gimme_json_for_portfolio'),

        (r'^profile/views/publish_citation_do$',
                'mysite.profile.views.publish_citation_do'),

        (r'^profile/views/delete_citation_do$',
                'mysite.profile.views.delete_citation_do'),

        (r'^profile/views/save_portfolio_entry_do$',
                'mysite.profile.views.save_portfolio_entry_do'),

        (r'^profile/views/delete_portfolio_entry_do$',
                'mysite.profile.views.delete_portfolio_entry_do'),

        (r'^people/portfolio/import/$',
                'mysite.profile.views.importer'),

        (r'^\+portfolio/editor/$',
                'mysite.profile.views.portfolio_editor'),

        (r'^\+portfolio/editor/test$',
                'mysite.profile.views.portfolio_editor_test'),

        (r'^profile/views/edit_info$', 'mysite.profile.views.edit_info'),

        (r'^profile/views/prepare_data_import_attempts_do$',
                'mysite.profile.views.prepare_data_import_attempts_do'),

        (r'^people/user_selected_these_dia_checkboxes$',
                'mysite.profile.views.user_selected_these_dia_checkboxes'),

        (r'^test_404$', handler404),

        (r'^search/people/(?P<property>[^/]+)/(?P<value>.+)$',
         'mysite.profile.views.permanent_redirect_to_people_search'),

        # favicon.ico. Someday this should be handled by Apache.
        (r'^(favicon.ico)',
         'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT + '/images'}),

        (r'^people/[$]username[/]*$', 'mysite.profile.views.dollar_username'),
        (r'^\+me$', 'mysite.profile.views.dollar_username', {}, 
                'oh_my_profile_redirect'),

        (r'^\+do/project.views.create_answer_do$', 'mysite.project.views.create_answer_do'),
        (r'^\+do/project.views.delete_paragraph_answer_do$', 'mysite.project.views.delete_paragraph_answer_do'),

        (r'^\+do/search.views.subscribe_to_bug_alert_do$', 'mysite.search.views.subscribe_to_bug_alert_do'),

        (r'^\+projects/', include('mysite.project.urls')),

        (r'^\+project/(?P<project__name>.+)', 'mysite.project.views.redirect_project_to_projects'),

        (r'^\+do/project.views.create_project_page_do$',
                'mysite.project.views.create_project_page_do'),

        (r'^\+yo_is_django_alive$', lambda x: HttpResponse('success')),

        (r'^\+bitesize$', lambda x: HttpResponseRedirect('/search/?q=&toughness=bitesize')),

        (r'^\+geocode$', 'mysite.base.views.geocode'),

                       (r'^hearch/', include('haystack.urls')),

        (r'^edit/name$', lambda x: redirect(to=mysite.account.views.edit_name, permanent=True)),

        (r'^\+v/nextsteps4helpers/$', 'mysite.project.views.nextsteps4helpers'),
        
        # This dangerous regex is last
        (r'^people/(?P<user_to_display__username>[^/]+)/$',
                'mysite.profile.views.display_person_web'),

        )

handler404 = 'mysite.base.views.page_not_found'

# vim: set ai ts=4 sts=4 et sw=4:
