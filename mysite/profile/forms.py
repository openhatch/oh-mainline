from django import forms
import models

class ProjectExpForm(forms.ModelForm):
    person_role = forms.CharField(label='Role')
    class Meta:
        model = models.ProjectExp
        exclude = ('person', 'project', 'man_months', 'primary_language')
