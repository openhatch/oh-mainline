import django.forms
import mysite.profile.models

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
    # FIXME: Align the attribute names with the model.
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
    def set_user(self, user):
        self.user = user
    def clean_project_exp_id(self):
        '''Note: I will explode violently if you
        have not set self.user.'''
        # Assert that self.user is set
        try:
            self.user
        except AttributeError:
            raise forms.ValidationError("For some reason, the programmer made a mistake, and I will blame you, the user.")
        # Now, check that there is a project_exp that is
        # owned by the user.
        inputted_id = self.cleaned_data['project_exp_id']
        try:
            p_e = mysite.profile.models.ProjectExp.objects.get(
                person__user=self.user, id=inputted_id)
        except mysite.profile.models.ProjectExp.DoesNotExist:
            raise django.forms.ValidationError("Somehow, you submitted regarding a project experience ID you do not own.")

        # so now we have a p_e. Jam it into cleaned_data.
        self.cleaned_data['project_exp'] = p_e
        return inputted_id
