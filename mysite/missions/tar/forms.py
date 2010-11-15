import django.forms

class TarExtractUploadForm(django.forms.Form):
    extracted_file = django.forms.FileField(error_messages={'required': 'No file was uploaded.'})

class TarUploadForm(django.forms.Form):
    tarfile = django.forms.FileField(error_messages={'required': 'No file was uploaded.'})
