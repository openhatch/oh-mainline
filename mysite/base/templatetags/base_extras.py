from django.conf import settings
from django import template
from django.utils.timesince import timesince
import time
import calendar
import datetime
import re
import urllib
import urlparse
import cgi
import mysite.project.controllers

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
        if 'the_user' in context and context['the_user'] and context['the_user'].is_staff:
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

show_common_data = register.tag(googleanalyticsjs)
