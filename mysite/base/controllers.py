from django.core.urlresolvers import reverse
import django.contrib.auth.views

notifications_dictionary = {
        "edit_password_done":
        "Your password has been changed.",

        "oops":
        """Couldn't find that pair of username and password. """
        "<a href='/account/forgot_pass/'>"
        "Click here if you forgot your password.</a>",

        "next":
        "You've got to be logged in to do that!",
        }

def get_notification_from_request(request):
    notification_id = request.GET.get('msg', None)
    if notification_id:
        try:
            notification_text = notifications_dictionary[notification_id]
        except KeyError:
            notification_text = ("Couldn't find notification text " 
                    + "for id = `%s`" % notification_id)
        return [ {
            'id': notification_id,
            'text': notification_text
            } ]
    else:
        return []

def mysql_regex_escape(s):
    ret = ''
    for letter in s:
        if letter == ']':
            ret += letter
        else:
            ret += '[' + letter + ']'
    return ret

# Thanks to zalun's comment at  
# http://stackoverflow.com/questions/41547/always-including-the-user-in-the-django-template-context
def add_user_variable_to_template_context(request):
    if hasattr(request, 'user'):
        return {'the_user': request.user}
    return {}

