from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'location', 'created_at')  
    list_filter = ('created_at', 'user')            
    search_fields = ('title', 'description', 'user__username')  
