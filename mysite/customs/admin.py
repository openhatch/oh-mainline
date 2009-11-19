from mysite.customs.models import WebResponse, RoundupBugTracker
from django.contrib import admin

for model in [WebResponse, RoundupBugTracker]:
    admin.site.register(model)
