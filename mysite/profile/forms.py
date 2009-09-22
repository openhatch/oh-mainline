import django.forms

class ProjectExpForm(django.forms.Form):
    project_name = django.forms.CharField(
        max_length=200,
        label='Project')
    involvement_description = django.forms.CharField(
        widget=django.forms.Textarea,
        required=False,
        label='Describe your involvement')
    citation_url = django.forms.URLField(
        max_length=200,
        label='Cite your involvement')
    


    
