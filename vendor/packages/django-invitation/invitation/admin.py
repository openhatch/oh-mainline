from django.contrib import admin
from invitation.models import InvitationKey

class InvitationKeyAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'from_user', 'date_invited', 'key_expired')

admin.site.register(InvitationKey, InvitationKeyAdmin)
