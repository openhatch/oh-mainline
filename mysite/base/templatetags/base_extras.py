# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2009, 2010, 2011 OpenHatch, Inc.
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

from django.conf import settings
from django import template
from django.utils.timesince import timesince
import time
import calendar
import datetime
import re
import os
import urlparse
import bleach
import mysite.project.controllers

from django.utils.html import * 

register = template.Library()

@register.filter
def timesince_terse(value, **args):
    if type(value) == time.struct_time:
        # icky, but do it
        secs_since_epoch = calendar.timegm(value)
        value = datetime.datetime.fromtimestamp(
            secs_since_epoch)

    string = timesince(value, **args)
    ret = string.split(", ")[0]
    if ret == '0 minutes':
        return 'just moments'
    return ret 

@register.filter
def enhance_next_to_annotate_it_with_newuser_is_true(value, **args):
    # value is a URL -- the value of "next"
    # here, we enhance it to get a query string indicating the user is a new user
    parts = urlparse.urlsplit(value)
    if parts.query:
        new_query = parts.query
        if 'newuser=true' not in new_query:
            new_query += '&newuser=true'
    else:
        new_query = 'newuser=true'
    return urlparse.urlunsplit(
        (parts[0], parts[1], parts[2], new_query, parts.fragment))

# Starting point for the below code 
# was http://www.djangosnippets.org/snippets/1656/
class ShowGoogleAnalyticsJS(template.Node):
    def render(self, context):
        code =  getattr(settings, "GOOGLE_ANALYTICS_CODE", False)
        if 'user' in context and context['user'] and context['user'].is_staff:
            return "<!-- Goggle Analytics not included because you are a staff user! -->"

        if not code:
            return "<!-- Goggle Analytics not included because you haven't set the settings.GOOGLE_ANALYTICS_CODE variable! -->"

        if settings.DEBUG:
            return "<!-- Goggle Analytics not included because you are in Debug mode! -->"

        return """
<script type="text/javascript">
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
</script>
<script type="text/javascript">
try {
var pageTracker = _gat._getTracker("CODE_HERE");
pageTracker._trackPageview();
} catch(err) {}</script>""".replace('CODE_HERE', code)

def googleanalyticsjs(parser, token):
    return ShowGoogleAnalyticsJS()

@register.filter
def get_answers_from_session(request):
    return mysite.project.controllers.get_unsaved_answers_from_session(request.session)

@register.filter
def get_project_display_names_to_help_from_session(request):
    return [p.display_name for p in
            mysite.project.controllers.get_wanna_help_queue_from_session(request.session)]

@register.filter
def bleach_urlize(text):
    '''Converts any URLs in text into clickable links.

    This adds rel=nofollow, and also sanitizes the input through bleach.'''
    linkified = bleach.linkify(unicode(text))
    cleaned = bleach.clean(linkified,
                           tags=['a',
                                 'p', 'div', 'br', 'span'
                                 'b', 'strong',
                                 'em', 'i'])
    return mark_safe(cleaned)

@register.filter
def urlize_without_escaping_percent_signs(text, trim_url_limit=None, nofollow=False, autoescape=False):
    """
    Converts any URLs in text into clickable links.

    Works on http://, https://, www. links and links ending in .org, .net or
    .com. Links can have trailing punctuation (periods, commas, close-parens)
    and leading punctuation (opening parens) and it'll still do the right
    thing.

    If trim_url_limit is not None, the URLs in link text longer than this limit
    will truncated to trim_url_limit-3 characters and appended with an elipsis.

    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.

    If autoescape is True, the link text and URLs will get autoescaped.
    """
    # I think this is a copy of a function in django.utils.html with one minor
    # change; see the comment below.

    trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
    safe_input = isinstance(text, SafeData)
    words = word_split_re.split(force_unicode(text))
    nofollow_attr = nofollow and ' rel="nofollow"' or ''
    for i, word in enumerate(words):
        match = None
        if '.' in word or '@' in word or ':' in word:
            match = punctuation_re.match(word)
        if match:
            lead, middle, trail = match.groups()
            # Make URL we want to point to.
            url = None
            if middle.startswith('http://') or middle.startswith('https://'):
                # The only difference between this function and the one
                # included in django.utils.html is the percent sign below.
                url = urlquote(middle, safe='/%&=:;#?+*')
            elif middle.startswith('www.') or ('@' not in middle and \
                    middle and middle[0] in string.ascii_letters + string.digits and \
                    (middle.endswith('.org') or middle.endswith('.net') or middle.endswith('.com'))):
                url = urlquote('http://%s' % middle, safe='/&=:;#?+*')
            elif '@' in middle and not ':' in middle and simple_email_re.match(middle):
                url = 'mailto:%s' % middle
                nofollow_attr = ''
            # Make link.
            if url:
                trimmed = trim_url(middle)
                if autoescape and not safe_input:
                    lead, trail = escape(lead), escape(trail)
                    url, trimmed = escape(url), escape(trimmed)
                middle = '<a href="%s"%s>%s</a>' % (url, nofollow_attr, trimmed)
                words[i] = mark_safe('%s%s%s' % (lead, middle, trail))
            else:
                if safe_input:
                    words[i] = mark_safe(word)
                elif autoescape:
                    words[i] = escape(word)
        elif safe_input:
            words[i] = mark_safe(word)
        elif autoescape:
            words[i] = escape(word)
    return u''.join(words)
urlize = allow_lazy(urlize, unicode)

show_common_data = register.tag(googleanalyticsjs)

@register.filter
def at(dict, key):
    """Usage: {{ dictionary|at:'key'}}"""
    if key in dict:
        return dict[key]
    return ''

@register.filter
def invitation_key2user(key):
    from invitation.models import InvitationKey
    return InvitationKey.objects.get(key=key).from_user

@register.filter
def truncate_chars(value, max_length):  
    max_length = int(max_length)
    if len(value) <= max_length:  
        return value  
  
    truncd_val = value[:max_length]  
    if value[max_length] != " ":  
        rightmost_space = truncd_val.rfind(" ")  
        if rightmost_space != -1:  
            truncd_val = truncd_val[:rightmost_space]  
  
    return truncd_val + "..." 

version_cache = {}

def version(path_string):
    """ Based on Stuart Colville's code at this blog post:
    http://muffinresearch.co.uk/archives/2008/04/08/automatic-asset-versioning-in-django/
    """
    if settings.ADD_VERSION_STRING_TO_IMAGES and (
            settings.ADD_VERSION_STRING_TO_IMAGES_IN_DEBUG_MODE
            or not settings.DEBUG):
        try:
            if path_string in version_cache:
                mtime = version_cache[path_string]
            else:
                try:
                    mtime = os.path.getmtime('%s%s' % (settings.MEDIA_ROOT_BEFORE_STATIC, path_string,))
                except (OSError, IOError):
                    mtime = 0
                version_cache[path_string] = mtime
                if settings.WHAT_SORT_OF_IMAGE_CACHE_BUSTING == 'filename':
                    rx = re.compile(r"^(.*)\.(.*?)$")
                    return rx.sub(r"\1.%d.\2" % mtime, path_string)
                else:
                    return "%s?%s"% (path_string, mtime)

        except:
            if settings.DEBUG:
                raise
            pass
    return path_string 

register.simple_tag(version)
