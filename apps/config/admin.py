# apps/config/admin.py
from django.contrib import admin
from django import forms
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin
from django.utils.translation import gettext_lazy as _
from .models import Page, SiteStyle, Menu, Redirect, CustomFieldValue, CustomField, FieldGroup


class CustomFieldValueInline(admin.TabularInline):
    model = CustomFieldValue
    extra = 1

@admin.register(Page)
class PageAdmin(MPTTModelAdmin):
    list_display = ('title', 'slug', 'status',  'scheduled_for', 'created_at', 'created_by', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at', 'scheduled_for')
    search_fields = ('title', 'content','name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    inlines = [CustomFieldValueInline]

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content', 'parent', 'status', 'scheduled_for')
        }),
        (_('SEO'), {
            'fields': ('meta_description', 'meta_keywords', 'canonical_url', 'robots'),
            'classes': ('collapse',)
        }),
        (_('Open Graph'), {
            'fields': ('og_title', 'og_description', 'og_image', 'og_type'),
            'classes': ('collapse',)
        }),
        (_('Schema.org'), {
            'fields': ('schema_type', 'schema_name', 'schema_description'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Se é uma nova página
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if isinstance(form, type):
            form = form()  # Instancia o formulário se for uma classe
        
        if 'status' in form.fields:
            form.fields['status'].widget.attrs['onchange'] = 'toggleScheduledFor(this.value);'
        return form

    class Media:
        js = ('js/admin_page.js',)
        
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)
     
@admin.register(Redirect)
class RedirectAdmin(admin.ModelAdmin):
    list_display = ('old_path', 'new_path', 'created_at')
    search_fields = ('old_path', 'new_path')
    readonly_fields = ('created_at',)
    
@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'field_type', 'required', 'group', 'order']
    list_filter = ['field_type', 'required', 'group']
    search_fields = ['name']
    # ... outros campos e configurações ...

@admin.register(FieldGroup)
class FieldGroupAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(SiteStyle)
class SiteStyleAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Permite apenas uma configuração de estilo
        return not SiteStyle.objects.exists()

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'parent', 'order', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'url')
    list_editable = ('order', 'active')