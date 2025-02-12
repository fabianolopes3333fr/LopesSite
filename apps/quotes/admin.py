from django.contrib import admin
from .models import Quote

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('name', 'service', 'area', 'status', 'created_at')
    list_filter = ('service', 'status', 'created_at')
    search_fields = ('name', 'email', 'service', 'details')
    readonly_fields = ('created_at',)
