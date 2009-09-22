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
    
class ProjectExpEditForm(django.forms.Form):
    # FIXME: Make this a ModelForm I guess.
    involvement_description = django.forms.CharField(
        widget=django.forms.Textarea,
        required=False,
        label='Describe your involvement')
    citation_url = django.forms.URLField(
        required=False,
        max_length=200,
        label='Cite your involvement')
    man_months=django.forms.IntegerField(
        required=False)
    primary_language=django.forms.CharField(
        max_length=200, required=False)
    project_exp_id=django.forms.IntegerField(
        required=False,
        widget=django.forms.widgets.HiddenInput)
