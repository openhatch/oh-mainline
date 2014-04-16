from django import forms

class IrcSessionPasswordForm(forms.Form):
    nick = forms.CharField()
    password = forms.CharField()
