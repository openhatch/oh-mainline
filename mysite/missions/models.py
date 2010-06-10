from django.db import models

class Step(models.Model):
    pass

class StepCompletion(models.Model):
    person = models.ForeignKey('profile.Person')
    step = models.ForeignKey('Step')

    class Meta:
        unique_together = ('person', 'step')
