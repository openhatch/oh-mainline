import django.forms
import mysite.search.models 

class BugAlertSubscriptionForm(django.forms.ModelForm):

    # Make these hidden inputs
    query_string = django.forms.CharField(widget=django.forms.HiddenInput())
    how_many_bugs_at_time_of_request = django.forms.CharField(widget=django.forms.HiddenInput())

    class Meta:
        model = mysite.search.models.BugAlert
        fields = ('query_string', 'email', 'how_many_bugs_at_time_of_request')
