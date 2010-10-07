import django.forms

import mysite.customs.models

class TrackerTypesForm(django.forms.Form):
    TRACKER_TYPES = (
            ('bugzilla', 'Bugzilla'),
            ('google', 'Google Code'),
            ('trac', 'Trac')
            )
    tracker_type = django.forms.ChoiceField(choices=TRACKER_TYPES)

class BugzillaTrackerForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.BugzillaTracker

class BugzillaUrlForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.BugzillaUrl
        exclude = ('tracker',)

class GoogleTrackerForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.GoogleTracker

class GoogleQueryForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.GoogleQuery
        exclude = ('tracker',)
