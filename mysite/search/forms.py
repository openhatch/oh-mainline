import django.forms
import mysite.search.models 

class BugAlertSubscriptionForm(django.forms.ModelForm):

    hidden_char_field = lambda: \
            django.forms.CharField(widget=django.forms.HiddenInput())

    query_string = hidden_char_field()
    how_many_bugs_at_time_of_request = hidden_char_field()

    email = django.forms.EmailField(
            label="Email address",
            error_messages={'invalid': 'This email address doesn\'t look right. Real or malarkey?'})

    class Meta:
        model = mysite.search.models.BugAlert
        fields = ('query_string', 'email', 'how_many_bugs_at_time_of_request')
