import django.forms

class PatchSingleUploadForm(django.forms.Form):
    patched_file = django.forms.FileField(error_messages={'required': 'No file was uploaded.'})

class DiffSingleUploadForm(django.forms.Form):
    diff = django.forms.CharField(error_messages={'required': 'No diff output was given.'}, widget=django.forms.Textarea())

class DiffRecursiveUploadForm(django.forms.Form):
    diff = django.forms.FileField(error_messages={'required': 'No file was uploaded.'})

class PatchRecursiveUploadForm(django.forms.Form):
    children_hats = django.forms.IntegerField()
    lizards_hats = django.forms.IntegerField()
