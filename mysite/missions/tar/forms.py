from mysite.missions.base.forms import *

class TarExtractUploadForm(forms.Form):
    extracted_file = forms.FileField(error_messages={'required': 'No file was uploaded.'})

class TarUploadForm(forms.Form):
    tarfile = forms.FileField(error_messages={'required': 'No file was uploaded.'})
