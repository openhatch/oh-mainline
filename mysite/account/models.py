from django.db import models

class InvitationRequest(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    """Possible other fields:
    - What open source projects are you involved with?
    - What do you wish were better or easier about open source?
    - "Free software" or "Open source"?"""
