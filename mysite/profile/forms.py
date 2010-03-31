import django.forms
import mysite.profile.models

class ManuallyAddACitationForm(django.forms.ModelForm):
    portfolio_entry = django.forms.ModelChoiceField(
            queryset=mysite.profile.models.PortfolioEntry.objects.all(), 
            widget=django.forms.HiddenInput())

    # The ID of the element in the portfolio editor that contains this form.
    form_container_element_id = django.forms.CharField(widget=django.forms.HiddenInput())
    #FIXME: Make is_published always true
    class Meta:
        model = mysite.profile.models.Citation
        fields = ('portfolio_entry', 'url', )

    def set_user(self, user):
        self.user = user

    def clean_portfolio_entry(self):
        '''Note: I will explode violently if you
        have not set self.user.'''
        # Assert that self.user is set
        try:
            self.user
        except AttributeError:
            raise django.forms.ValidationError("For some reason, the programmer made a mistake, "
                    "and I will blame you, the user.")

        # Check that the user owns this portfolio entry.
        pf_entry = self.cleaned_data['portfolio_entry'] # By now this is an object, not an ID.
        if pf_entry.person.user == self.user:
            return pf_entry
        else:
            raise django.forms.ValidationError("Somehow, you submitted "
                    "regarding a portfolio entry that you do not own.")

class EditInfoForm(django.forms.Form):
  bio = django.forms.CharField(required=False, widget=django.forms.Textarea())
  homepage_url = django.forms.URLField(required=False)
  understands = django.forms.CharField(required=False, widget=django.forms.Textarea())
  understands_not = django.forms.CharField(required=False, widget=django.forms.Textarea())
  studying = django.forms.CharField(required=False, widget=django.forms.Textarea())
  can_pitch_in = django.forms.CharField(required=False, widget=django.forms.Textarea())
  can_mentor = django.forms.CharField(required=False, widget=django.forms.Textarea())

class ContactBlurbForm(django.forms.Form):
  contact_blurb = django.forms.CharField(required=False, widget=django.forms.Textarea())

# vim: set nu:
