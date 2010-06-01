from django.db import models

class MissionStep(models.Model):
    pass

class MissionStepCompletion(models.Model):
    person = models.ForeignKey('profile.Person')
    step = models.ForeignKey('MissionStep')

    class Meta:
        unique_together = ('person', 'step')
