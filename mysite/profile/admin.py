from mysite.profile.models import Person, DataImportAttempt, Tag, TagType, PortfolioEntry, Citation
from django.contrib import admin

admin.site.register(Person)
admin.site.register(DataImportAttempt)
admin.site.register(Tag)
admin.site.register(TagType)
admin.site.register(PortfolioEntry)
admin.site.register(Citation)
