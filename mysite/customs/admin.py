import mysite.customs.models
from django.contrib import admin

for model in [mysite.customs.models.WebResponse]:
    admin.site.register(model)
