import django.forms
import mysite.search.models

class WannaHelpForm(django.forms.Form):
    project = django.forms.ModelChoiceField(mysite.search.models.Project.objects.all())
