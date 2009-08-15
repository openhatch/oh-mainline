from django.db import models
from django.contrib.auth.models import User

class Bug(models.Model):
    """ A bug in OpenHatch, filed through SenseKnocker. """
    # {{{
    user = models.ForeignKey(User)
    background = models.TextField(
            verbose_name='What were you doing at the time?')
    expected_behavior = models.TextField(
            verbose_name='What did you expect to happen?')
    actual_behavior = models.TextField(
            verbose_name='What actually happened?')

    def __unicode__(self):
        return "<SenseKnocker.Bug pk=%d user__username=%s>" % (
                self.pk, user.username)
    # }}}

# vim: set ai ts=4 sw=4 et:
