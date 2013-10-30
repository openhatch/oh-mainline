# This file is part of OpenHatch.
# Copyright (C) 2009, 2010 OpenHatch, Inc.
# Copyright (C) 2010 John Stumpo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from speechd_config.config import question

import django.forms
from mysite.base.fields import QuestionFormField
import mysite.profile.models
from mysite.profile.models import FormResponse, FormAnswer, FormQuestion
from mysite.search.models import Project


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

    person = None
    questions = []
    responses = []

    def __select_initial_response__(self, field, question):
        initial = []
        for a, response in enumerate(self.responses):
            if response.question.id == question.id:
                initial.append(response.value)
                if field.type != 'multi':
                    break
        if field.type == 'multi':
            field.initial = initial
        else:
            if len(initial) > 0:
                field.initial = str(initial[0]).replace('\\r\\n', '\n').replace('\\n', '\n')

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop('person')
        self.questions = FormQuestion.objects.all()
        self.responses = FormResponse.objects.filter(person__pk=self.person.id)
        super(EditInfoForm, self).__init__(*args, **kwargs)

        for i, question in enumerate(self.questions):
            answers = FormAnswer.objects.filter(question__pk=question.id)
            self.fields['question_%s' % question.id] = QuestionFormField(required=question.required, type=question.type,
                                                                     label=question.name, answers=answers)
            self.__select_initial_response__(self.fields['question_%s' % question.id], question)


class ContactBlurbForm(django.forms.Form):
    contact_blurb = django.forms.CharField(required=False, widget=django.forms.Textarea())

class UseDescriptionFromThisPortfolioEntryForm(django.forms.ModelForm):
    class Meta:
        model = mysite.profile.models.PortfolioEntry
        fields = ('use_my_description', )

class DeleteUser(django.forms.Form):
    username = django.forms.CharField(required=True,
                                      widget=django.forms.Textarea())

class SelectProjectsModelMultipleChoiceField(django.forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name

class SelectProjectsForm(django.forms.Form):
    Projects = SelectProjectsModelMultipleChoiceField(
        required=False, queryset=Project.objects.all().order_by('name'),widget=django.forms.CheckboxSelectMultiple)

# vim: set nu:
