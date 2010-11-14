from mysite.missions.base.forms import *

class PatchSingleUploadForm(forms.Form):
    patched_file = forms.FileField(error_messages={'required': 'No file was uploaded.'})

class DiffSingleUploadForm(forms.Form):
    diff = forms.CharField(error_messages={'required': 'No diff output was given.'}, widget=forms.Textarea())

class DiffRecursiveUploadForm(forms.Form):
    diff = forms.FileField(error_messages={'required': 'No file was uploaded.'})

class PatchRecursiveUploadForm(forms.Form):
    children_hats = forms.IntegerField()
    lizards_hats = forms.IntegerField()
