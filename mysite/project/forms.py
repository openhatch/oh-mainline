import django.forms
import mysite.search.models

class WannaHelpForm(django.forms.Form):
    project = django.forms.ModelChoiceField(mysite.search.models.Project.objects.all())
    from_offsite = django.forms.BooleanField(required=False)

class ProjectForm(django.forms.ModelForm):

    def clean_name(self):

        proposed_name = self.cleaned_data['name'].strip()

        # Only save if nothing but capitalization was changed
        if (proposed_name.lower() != self.instance.name.lower()):
            raise django.forms.ValidationError("You can only make changes to the capitalization of the name.")
        return proposed_name

    def clean_language(self):
        lang = self.cleaned_data['language']

        # Try to use the capitalization of a language already assigned to a project
        matching_projects = mysite.search.models.Project.objects.filter(language__iexact=lang)
        if matching_projects:
            return matching_projects[0].language
        return lang

    class Meta:
        model = mysite.search.models.Project
        fields = ('name', 'language', 'icon_raw')
