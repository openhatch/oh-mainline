import django.contrib.auth.forms
from django.contrib.auth.models import User
import django.forms

class UserCreationFormWithEmail(
        django.contrib.auth.forms.UserCreationForm):
    email = django.forms.EmailField()
    class Meta:
        model = django.contrib.auth.models.User
        fields = ('username', 'email', 'password1')

    def __init__(self, *args, **kw):
        super(django.contrib.auth.forms.UserCreationForm,
                self).__init__(*args, **kw)

    def clean_email(self):
        """Verify that their email is unique."""
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise django.forms.ValidationError(
            "A user with that email already exists.")
