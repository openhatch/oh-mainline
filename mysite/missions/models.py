from django.db import models

class Step(models.Model):
    name = models.CharField(max_length=255, unique=True)

class StepCompletion(models.Model):
    person = models.ForeignKey('profile.Person')
    step = models.ForeignKey('Step')

    class Meta:
        unique_together = ('person', 'step')
