from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from registration.forms import RegistrationFormTermsOfService
from invitation.views import invite, invited, register

urlpatterns = patterns('',
    url(r'^invite/complete/$',
                direct_to_template,
                {'template': 'invitation/invitation_complete.html'},
                name='invitation_complete'),
    url(r'^invite/$',
                invite,
                name='invitation_invite'),
    url(r'^invited/(?P<invitation_key>\w+)/$', 
                invited,
                name='invitation_invited'),
    url(r'^register/$',
                register,
                name='registration_register'),
)
