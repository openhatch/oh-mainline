from django.contrib.sessions.models import Session
import datetime


def clear_user_sessions(user, session_to_omit=None):
    user_sessions = []
    for session in Session.objects.filter(expire_date__gte=datetime.datetime.now()):
        # This uses session.get_decoded(), which is slow. Currently, Django
        # does not provide a built-in way to access a user's sessions
        if user.pk == session.get_decoded().get('_auth_user_id'):
            user_sessions.append(session.pk)
    session_list = Session.objects.filter(pk__in=user_sessions)
    if session_to_omit is not None:
        session_list = session_list.exclude(pk=session_to_omit.session_key)
    session_list.delete()
