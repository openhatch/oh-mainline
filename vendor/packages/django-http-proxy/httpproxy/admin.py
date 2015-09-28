from django.contrib import admin

from httpproxy.models import Request, RequestParameter, Response


class ResponseInline(admin.StackedInline):
    model = Response


class RequestParameterInline(admin.TabularInline):
    model = RequestParameter
    extra = 1


class RequestAdmin(admin.ModelAdmin):
    list_display = ('method', 'domain', 'port', 'path', 'querystring_display', 'date')
    list_filter = ('method', 'domain', 'port')
    inlines = (RequestParameterInline, ResponseInline)


class ResponseAdmin(admin.ModelAdmin):
    list_display = ('request_domain', 'request_path', 'request_querystring', 'status', 'content_type')
    list_filter = ('status', 'content_type')


admin.site.register(Request, RequestAdmin)
admin.site.register(Response, ResponseAdmin)
