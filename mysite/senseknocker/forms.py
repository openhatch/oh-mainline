from django import forms
import models

class BugForm(forms.ModelForm):
    class Meta:
        model = models.Bug
