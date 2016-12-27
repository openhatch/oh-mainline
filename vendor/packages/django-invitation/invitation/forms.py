from django import forms

class InvitationKeyForm(forms.Form):
    email = forms.EmailField()
    