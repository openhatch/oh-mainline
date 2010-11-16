import django.forms

class ExtractUploadForm(django.forms.Form):
    extracted_file = django.forms.FileField(error_messages={'required': 'No file was uploaded.'})

class UploadForm(django.forms.Form):
    tarfile = django.forms.FileField(error_messages={'required': 'No file was uploaded.'})
