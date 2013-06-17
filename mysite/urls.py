# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2010, 2011 Jack Grigg
# Copyright (C) 2009 Karen Rustad
# Copyright (C) 2009, 2010 OpenHatch, Inc.
# Copyright (C) 2010 John Stumpo
# Copyright (C) 2011 Krzysztof Tarnowski (krzysztof.tarnowski@ymail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls.defaults import patterns, url, include, handler404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import redirect

from django.conf import settings

from django.contrib import admin
admin.autodiscover()

import mysite.account.forms

import django_authopenid.views

#used for the robots.txt redirection
from django.views.generic.simple import direct_to_template

from voting.views import vote_on_object

import mysite.account.views
import mysite.profile.views
import mysite.customs.api
import mysite.profile.api
import mysite.missions.svn.views
import mysite.missions.setup.views

from mysite.base.feeds import RecommendedBugsFeed, RecentActivityFeed

feeds = {
        'recbugs': RecommendedBugsFeed,
        'activity': RecentActivityFeed,
        }

urlpatterns = patterns('',
        ### Okay, sometimes people link /, or /) because of bad linkification
        ### if so, just permit it as a redirect.
        (r'^,$', lambda x: HttpResponsePermanentRedirect('/')),
        (r'^\)$', lambda x: HttpResponsePermanentRedirect('/')),

        (r'^\+meta/', 'mysite.base.views.meta'),

        (r'^\+api/v1/profile/',
         include(mysite.profile.api.PortfolioEntryResource().urls)),

        (r'^\+api/v1/delete_user_for_being_spammy/$',
            mysite.profile.views.delete_user_for_being_spammy),

        (r'^\+api/v1/customs/',
         include(mysite.customs.api.TrackerModelResource().urls)),

        (r'^\+test_email_re_projects/', 'mysite.base.views.test_email_re_projects'),

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

        # Feed URL pattern
        url(r'^\+feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}, name='oh_feed_url'),

        # Mission-related URLs
        (r'^missions/$', 'mysite.missions.base.views.main_page'),
        (r'^missions/tar$', 'mysite.missions.tar.views.about'),
        (r'^missions/tar/reset$', 'mysite.missions.tar.views.reset'),
        (r'^missions/tar/unpacking$', 'mysite.missions.tar.views.unpacking'),
        (r'^missions/tar/creating$', 'mysite.missions.tar.views.creating'),
        (r'^missions/tar/hints$', 'mysite.missions.tar.views.hints'),
        (r'^missions/tar/upload$', 'mysite.missions.tar.views.upload'),
        (r'^missions/tar/downloadfile/(?P<name>.*)', 'mysite.missions.tar.views.file_download'),
        (r'^missions/tar/ghello-0.4.tar.gz', 'mysite.missions.tar.views.download_tarball_for_extract_mission'),
        (r'^missions/tar/extractupload', 'mysite.missions.tar.views.extract_mission_upload'),

        (r'^missions/diffpatch$', 'mysite.missions.diffpatch.views.about'),
        (r'^missions/diffpatch/single_diff$', 'mysite.missions.diffpatch.views.single_file_diff'),
        (r'^missions/diffpatch/single_patch$', 'mysite.missions.diffpatch.views.single_file_patch'),
        (r'^missions/diffpatch/recursive_diff$', 'mysite.missions.diffpatch.views.recursive_diff'),
        (r'^missions/diffpatch/recursive_patch$', 'mysite.missions.diffpatch.views.recursive_patch'),
        (r'^missions/diffpatch/patchsingle/oven-pancake.txt', 'mysite.missions.diffpatch.views.patchsingle_get_original_file'),
        (r'^missions/diffpatch/patchsingle/add-oven-temp.patch$', 'mysite.missions.diffpatch.views.patchsingle_get_patch'),
        (r'^missions/diffpatch/patchsingle/submit$', 'mysite.missions.diffpatch.views.patchsingle_submit'),
        (r'^missions/diffpatch/diffsingle/nutty-pancake.txt$', 'mysite.missions.diffpatch.views.diffsingle_get_original_file'),
        (r'^missions/diffpatch/diffsingle/submit$', 'mysite.missions.diffpatch.views.diffsingle_submit'),
        (r'^missions/diffpatch/diffrecursive/recipes.tar.gz$', 'mysite.missions.diffpatch.views.diffrecursive_get_original_tarball'),
        (r'^missions/diffpatch/diffrecursive/submit$', 'mysite.missions.diffpatch.views.diffrecursive_submit'),
        (r'^missions/diffpatch/patchrecursive/recipes.patch$', 'mysite.missions.diffpatch.views.patchrecursive_get_patch'),
        (r'^missions/diffpatch/patchrecursive/submit$', 'mysite.missions.diffpatch.views.patchrecursive_submit'),

        (r'^missions/svn$', mysite.missions.svn.views.MainPage.as_view(), None, 'svn_main_page'),
        (r'^missions/svn/description$', mysite.missions.svn.views.LongDescription.as_view(), None, 'svn_long_description'),
        (r'^missions/svn/checkout$', mysite.missions.svn.views.Checkout.as_view(), None, 'svn_checkout'),
        (r'^missions/svn/diff$', mysite.missions.svn.views.Diff.as_view(), None, 'svn_diff'),
        (r'^missions/svn/commit$', mysite.missions.svn.views.Commit.as_view(), None, 'svn_commit'),
        (r'^missions/svn/resetrepo$', 'mysite.missions.svn.views.resetrepo'),
        (r'^missions/svn/checkout/submit$', 'mysite.missions.svn.views.checkout_submit'),
        (r'^missions/svn/diff/submit$', 'mysite.missions.svn.views.diff_submit'),
        (r'^missions/svn/commit/poll$', 'mysite.missions.svn.views.commit_poll'),

        (r'^missions/git$', 'mysite.missions.git.views.main_page'),
        (r'^missions/git/description$', 'mysite.missions.git.views.long_description'),
        (r'^missions/git/description/submit$', 'mysite.missions.git.views.long_description_submit'),
        (r'^missions/git/checkout$', 'mysite.missions.git.views.checkout'),
        (r'^missions/git/resetrepo$', 'mysite.missions.git.views.resetrepo'),
        (r'^missions/git/checkout/submit$', 'mysite.missions.git.views.checkout_submit'),
        (r'^missions/git/diff$', 'mysite.missions.git.views.diff'),
        (r'^missions/git/diff/submit$', 'mysite.missions.git.views.diff_submit'),
        (r'^missions/git/rebase$', 'mysite.missions.git.views.rebase'),
        (r'^missions/git/rebase/submit$', 'mysite.missions.git.views.rebase_submit'),

        (r'^missions/windows-setup',
         include(mysite.missions.setup.views.WindowsSetup.urls())),

        # Customs-related URLs
        (r'^customs/$', 'mysite.customs.views.list_trackers'),
        (r'^customs/add/(?P<tracker_type>\w*)$', 'mysite.customs.views.add_tracker'),
        (r'^customs/add/(?P<tracker_type>\w*)/do$', 'mysite.customs.views.add_tracker_do'),
        (r'^customs/add/(?P<tracker_type>\w*)/(?P<tracker_id>\d+)/(?P<tracker_name>[^/]+)/url$', 'mysite.customs.views.add_tracker_url'),
        (r'^customs/add/(?P<tracker_type>\w*)/(?P<tracker_id>\d+)/(?P<tracker_name>.+)/url/do$', 'mysite.customs.views.add_tracker_url_do'),
        (r'^customs/edit/(?P<tracker_type>\w*)/(?P<tracker_id>\d+)/(?P<tracker_name>.+)/url/(?P<url_id>\d*)/do$', 'mysite.customs.views.edit_tracker_url_do'),
        (r'^customs/edit/(?P<tracker_type>\w*)/(?P<tracker_id>\d+)/(?P<tracker_name>.+)/url/(?P<url_id>\d+)$', 'mysite.customs.views.edit_tracker_url'),
        (r'^customs/edit/(?P<tracker_type>\w*)/(?P<tracker_id>\d+)/(?P<tracker_name>.+)/do$', 'mysite.customs.views.edit_tracker_do'),
        (r'^customs/edit/(?P<tracker_type>\w*)/(?P<tracker_id>\d+)/(?P<tracker_name>.+)$', 'mysite.customs.views.edit_tracker'),
        (r'^customs/delete/(?P<tracker_type>\w*)/(?P<tracker_id>\d+)/(?P<tracker_name>.+)$', 'mysite.customs.views.delete_tracker'),
        (r'^customs/delete/(?P<tracker_type>\w*)/(?P<tracker_id>\d+)/(?P<tracker_name>.+)/do$', 'mysite.customs.views.delete_tracker_do'),
        (r'^customs/delete_url/(?P<tracker_type>\w*)/(?P<tracker_id>\d+)/(?P<tracker_name>.+)/url/(?P<url_id>\d*)$', 'mysite.customs.views.delete_tracker_url'),
        (r'^customs/delete_url/(?P<tracker_type>\w*)/(?P<tracker_id>\d+)/(?P<tracker_name>.+)/url/(?P<url_id>\d*)/do$', 'mysite.customs.views.delete_tracker_url_do'),

        # Invitation-related URLs
        (r'^invitation/', include('invitation.urls')),

        (r'^$', 'mysite.base.views.home'),
        (r'^\+theme-stubs/wordpress/index$', 'mysite.base.views.wordpress_index'),

        (r'^\+landing/import$', 'mysite.base.views.landing_for_documenters'),
        (r'^\+landing/opps$', 'mysite.base.views.landing_for_opp_hunters'),
        (r'^\+landing/projects$', 'mysite.base.views.landing_for_project_maintainers'),

        (r'^search/$', 'mysite.search.views.fetch_bugs'),
        (r'^admin/', include(admin.site.urls)),
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),

        (r'^people/$',
            'mysite.profile.views.people'),

        (r'^\+profile_api/location_data/$',
            mysite.profile.views.LocationDataApiView.as_view()),

        (r'^\+people/list/$', lambda x: HttpResponsePermanentRedirect('/people/')),

        (r'^account/proxyconnect-sso$', 'mysite.account.views.proxyconnect_sso'),

        (r'^account/forgot_pass/$',
            'django.contrib.auth.views.password_reset', {
                'template_name': 'account/password_reset.html',
                'email_template_name': 'account/password_reset_email.html'
                },
            "oh_forgot_pass"),

        (r'^account/catch-me$', 'mysite.account.views.catch_me'),

        (r'^account/login/$', 'mysite.account.views.login',
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
        url(r'^openid/signin/$', django_authopenid.views.signin, name='user_signin'),

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

        (r'^\+profile/bug_recommendation_list_as_template_fragment$',
                'mysite.profile.views.bug_recommendation_list_as_template_fragment'),

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

        (r'^projects/', include('mysite.project.urls')),

        (r'^\+projects/', lambda x: HttpResponsePermanentRedirect('/projects/')),

        (r'^ projects/', lambda x: HttpResponsePermanentRedirect('/projects/')),

        (r'^\+project/(?P<project__name>.+)', 'mysite.project.views.redirect_project_to_projects'),

        (r'^\+do/project.views.create_project_page_do$',
                'mysite.project.views.create_project_page_do'),

        (r'^\+yo_is_django_alive$', lambda x: HttpResponse('success')),

        (r'^\+bitesize$', lambda x: HttpResponseRedirect('/search/?q=&toughness=bitesize')),

        (r'^\+geocode$', 'mysite.base.views.geocode'),

        (r'^edit/name$', lambda x: redirect(to=mysite.account.views.edit_name, permanent=True)),

        (r'^\+v/nextsteps4helpers/$', 'mysite.project.views.nextsteps4helpers'),

        #regex for the robots.txt file, for search engine exclusion
        (r'^robots\.txt$', direct_to_template, {'template': 'robots.txt', 'mimetype': 'text/plain'}),

        # the OpenHatch guide
        (r'^guide/$', direct_to_template, {'template': 'base/guide.html'}),

        # the OpenHatch events page
        (r'^events/$', direct_to_template, {'template': 'base/events.html'}),

        # the OpenHatch sponsors page
        (r'^sponsors/$', direct_to_template, {'template': 'base/sponsors.html'}),

        # the OpenHatch donate page
        (r'^donate/$', direct_to_template, {'template': 'base/donate.html'}),
        # the OpenHatch donate page
        (r'^donate/t-shirts/$', direct_to_template, {'template': 'base/shirts.html'}),

        # This dangerous regex is last
        (r'^people/(?P<user_to_display__username>[^/]+)/$',
                'mysite.profile.views.display_person_web'),

        )

handler404 = 'mysite.base.views.page_not_found'

# vim: set ai ts=4 sts=4 et sw=4:
