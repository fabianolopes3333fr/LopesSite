from django.contrib import admin
from .models import Contact, CompanyInfo

@admin.register(Contact)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'postal_code', 'phone', 'email')
    search_fields = ('name', 'city', 'postal_code')
