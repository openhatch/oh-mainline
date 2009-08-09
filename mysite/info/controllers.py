notifications_dictionary = {
        "edit_password_done":
        "Your password has been changed.",

        "oops":
        """Couldn't find that pair of username and password.
        Did you type your password correctly?""",

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
