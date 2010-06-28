from django import forms

class TarExtractUploadForm(forms.Form):
    extracted_file = forms.FileField(error_messages={'required': 'No file was uploaded.'})

class TarUploadForm(forms.Form):
    tarfile = forms.FileField(error_messages={'required': 'No file was uploaded.'})

class PatchSingleUploadForm(forms.Form):
    patched_file = forms.FileField(error_messages={'required': 'No file was uploaded.'})
