# Work of Dorsaf - Interface d'administration des signalements
from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_object', 'report_type', 'status', 'reporter', 'created_at')
    list_filter = ('status', 'report_type', 'created_at')
    search_fields = ('message', 'reporter__username', 'content_type__model')
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    readonly_fields = ('content_object', 'reporter', 'created_at', 'updated_at')