from profile.models import DataImportAttempt
dias = DataImportAttempt.objects.all()
for d in dias:
    d.delete()
