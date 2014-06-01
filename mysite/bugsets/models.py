from django.db import models

class BugSet(models.Model):
    name = models.CharField(max_length=200)
    #date = models.DateTimeField(auto_now_add=True)
