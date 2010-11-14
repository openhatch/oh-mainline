from mysite.missions.base.forms import *

class SvnCheckoutForm(forms.Form):
    secret_word = forms.CharField(error_messages={'required': 'No secret word was given.'})

class SvnDiffForm(forms.Form):
    diff = forms.CharField(error_messages={'required': 'No svn diff output was given.'}, widget=forms.Textarea())
