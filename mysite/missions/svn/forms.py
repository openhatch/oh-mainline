import django.forms

class CheckoutForm(django.forms.Form):
    secret_word = django.forms.CharField(error_messages={'required': 'No secret word was given.'})

class DiffForm(django.forms.Form):
    diff = django.forms.CharField(error_messages={'required': 'No svn diff output was given.'}, widget=django.forms.Textarea())
