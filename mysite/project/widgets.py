from file_resubmit.admin import AdminResubmitFileWidget
from file_resubmit.admin import mark_safe
from django.forms.widgets import CheckboxInput
from django.forms.widgets import ClearableFileInput
from django.utils.html import conditional_escape

class IconWidget(AdminResubmitFileWidget):
    input_text = ClearableFileInput.input_text
    clear_checkbox_label = ClearableFileInput.clear_checkbox_label

    template_with_clear = '%(clear)s <label for="%(clear_checkbox_id)s">%(clear_checkbox_label)s</label>'
    template_with_initial = '<div>%(initial)s %(clear_template)s<br />%(input_text)s:</div>%(input)s'

    def render(self, name, value, attrs=None):
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
        }
        template = '%(input)s'
        substitutions['input'] = super(ClearableFileInput, self).render(name, value, attrs)

        if value and hasattr(value, "url"):
            template = self.template_with_initial
            substitutions['initial'] = str.format('<img width="64" src="{0}" />',
                                                   value.url)
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                substitutions['clear_template'] = self.template_with_clear % substitutions

        return mark_safe(template % substitutions)