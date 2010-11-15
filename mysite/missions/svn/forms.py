import django.forms

class SvnCheckoutForm(django.forms.Form):
    secret_word = django.forms.CharField(error_messages={'required': 'No secret word was given.'})

class SvnDiffForm(django.forms.Form):
    diff = django.forms.CharField(error_messages={'required': 'No svn diff output was given.'}, widget=django.forms.Textarea())
