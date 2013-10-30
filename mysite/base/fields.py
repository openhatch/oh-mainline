from django.core import validators
from django.forms import Field, TextInput, Textarea, RadioSelect, CheckboxSelectMultiple
import django.forms
from file_resubmit import AdminResubmitFileWidget


class QuestionFormField(Field):
    type = None
    answers = []
    extra_validators = []

    def __init__(self, *args, **kwargs):
        self.type = kwargs.pop('type', None)
        self.answers = kwargs.pop('answers', [])
        if self.type == 'text':
            self.widget = TextInput()
        if self.type == 'textarea':
            self.widget = Textarea()
        if self.type == 'single' or self.type == 'multi':
            answers = []
            for a, answer in enumerate(self.answers):
                answers.append((answer.value, answer.value))
            if self.type == 'multi':
                self.widget = CheckboxSelectMultiple(choices=answers)
            else:
                self.widget = RadioSelect(choices=answers)
        if self.type == 'boolean':
            self.widget = RadioSelect(choices=[(True,'Yes'),(False,'No')])
        if self.type == 'url':
            self.widget = django.forms.TextInput()
            #self.extra_validators.append(validators.URLValidator())
        if self.type == 'file':
            self.widget = AdminResubmitFileWidget()

        super(QuestionFormField, self).__init__(*args, **kwargs)
        for validator in self.extra_validators:
            self.validators.append(validator)
