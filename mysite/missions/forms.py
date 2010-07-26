from django import forms

class TarExtractUploadForm(forms.Form):
    extracted_file = forms.FileField(error_messages={'required': 'No file was uploaded.'})

class TarUploadForm(forms.Form):
    tarfile = forms.FileField(error_messages={'required': 'No file was uploaded.'})

class PatchSingleUploadForm(forms.Form):
    patched_file = forms.FileField(error_messages={'required': 'No file was uploaded.'})

class DiffSingleUploadForm(forms.Form):
    diff = forms.CharField(error_messages={'required': 'No diff output was given.'}, widget=forms.Textarea())

class DiffRecursiveUploadForm(forms.Form):
    diff = forms.FileField(error_messages={'required': 'No file was uploaded.'})

class PatchRecursiveUploadForm(forms.Form):
    children_hats = forms.IntegerField()
    lizards_hats = forms.IntegerField()

class SvnCheckoutForm(forms.Form):
    secret_word = forms.CharField(error_messages={'required': 'No secret word was given.'})

class SvnDiffForm(forms.Form):
    diff = forms.CharField(error_messages={'required': 'No svn diff output was given.'}, widget=forms.Textarea())
