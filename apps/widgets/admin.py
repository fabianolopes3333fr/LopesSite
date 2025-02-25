# Lopes/widgets/admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django import forms
from mptt.admin import MPTTModelAdmin
from .models import (
    TemplateCategory, 
    TemplateType, 
    DjangoTemplate, 
    TemplateRegion,
    LayoutTemplate, 
    ComponentTemplate, 
    ComponentInstance,
    WidgetArea, 
    Widget, 
    WidgetInstance
)
import json


class JsonWidget(forms.Textarea):
    """
    Widget personalizado para edição de campos JSON com validação básica.
    """
    def __init__(self, attrs=None):
        default_attrs = {'rows': 10, 'class': 'json-editor'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def format_value(self, value):
        if value is None or value == '':
            return '{}'
        if isinstance(value, str):
            try:
                return json.dumps(json.loads(value), indent=2)
            except:
                return value
        return json.dumps(value, indent=2)


class TemplateCategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'slug', 'icon', 'parent', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('name', 'slug', 'description', 'icon', 'parent', 'is_active')
        }),
        (_('Informações de Auditoria'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class TemplateTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'type', 'category', 'icon', 'is_active')
    list_filter = ('type', 'category', 'is_active')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('name', 'slug', 'description', 'type', 'category', 'icon', 'is_active')
        }),
        (_('Informações de Auditoria'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class TemplateRegionInline(admin.TabularInline):
    model = TemplateRegion
    extra = 1
    fields = ('name', 'slug', 'description', 'order', 'is_required', 'max_blocks')
    prepopulated_fields = {'slug': ('name',)}


class WidgetAreaInline(admin.TabularInline):
    model = WidgetArea
    extra = 1
    fields = ('name', 'slug', 'description', 'order', 'css_classes', 'max_widgets')
    prepopulated_fields = {'slug': ('name',)}


class DjangoTemplateAdminForm(forms.ModelForm):
    class Meta:
        model = DjangoTemplate
        fields = '__all__'
        widgets = {
            'default_context': JsonWidget(),
        }


class DjangoTemplateAdmin(admin.ModelAdmin):
    form = DjangoTemplateAdminForm
    list_display = ('name', 'slug', 'file_path', 'type', 'preview_thumbnail', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('name', 'slug', 'description', 'file_path')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TemplateRegionInline, WidgetAreaInline]
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('name', 'slug', 'description', 'type', 'file_path', 'is_active')
        }),
        (_('Contexto e Preview'), {
            'fields': ('default_context', 'preview_image')
        }),
        (_('Informações de Auditoria'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def preview_thumbnail(self, obj):
        if obj.preview_image:
            return format_html('<img src="{}" width="100" height="auto" />', obj.preview_image.url)
        return '-'
    preview_thumbnail.short_description = _('Preview')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class LayoutTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'template', 'header', 'footer', 'sidebar', 'is_default', 'is_active')
    list_filter = ('template', 'is_default', 'is_active')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('name', 'slug', 'description', 'is_active')
        }),
        (_('Composição do Layout'), {
            'fields': ('template', 'header', 'footer', 'sidebar', 'css_classes', 'is_default')
        }),
        (_('Aparência'), {
            'fields': ('thumbnail',)
        }),
        (_('Informações de Auditoria'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class ComponentTemplateAdminForm(forms.ModelForm):
    class Meta:
        model = ComponentTemplate
        fields = '__all__'
        widgets = {
            'template_code': forms.Textarea(attrs={'rows': 15, 'class': 'html-editor'}),
            'css_code': forms.Textarea(attrs={'rows': 10, 'class': 'css-editor'}),
            'js_code': forms.Textarea(attrs={'rows': 10, 'class': 'js-editor'}),
            'default_context': JsonWidget(),
        }


class ComponentTemplateAdmin(admin.ModelAdmin):
    form = ComponentTemplateAdminForm
    list_display = ('name', 'slug', 'component_type', 'category', 'preview_thumbnail', 'is_active')
    list_filter = ('component_type', 'category', 'is_active')
    search_fields = ('name', 'slug', 'description', 'template_code')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('name', 'slug', 'description', 'component_type', 'category', 'icon', 'is_active')
        }),
        (_('Código do Componente'), {
            'fields': ('template_code', 'css_code', 'js_code', 'default_context')
        }),
        (_('Aparência'), {
            'fields': ('thumbnail',)
        }),
        (_('Informações de Auditoria'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def preview_thumbnail(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="100" height="auto" />', obj.thumbnail.url)
        return '-'
    preview_thumbnail.short_description = _('Preview')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class ComponentInstanceAdminForm(forms.ModelForm):
    class Meta:
        model = ComponentInstance
        fields = '__all__'
        widgets = {
            'context_data': JsonWidget(),
            'visibility_rules': JsonWidget(),
            'custom_css': forms.Textarea(attrs={'rows': 5, 'class': 'css-editor'}),
        }


class ComponentInstanceAdmin(admin.ModelAdmin):
    form = ComponentInstanceAdminForm
    list_display = ('component', 'region', 'order', 'is_visible')
    list_filter = ('region__template', 'component__component_type', 'is_visible')
    search_fields = ('component__name', 'region__name', 'custom_classes')
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('component', 'region', 'order', 'is_visible')
        }),
        (_('Personalização'), {
            'fields': ('context_data', 'custom_css', 'custom_classes')
        }),
        (_('Visibilidade Condicional'), {
            'fields': ('visibility_rules',)
        }),
        (_('Informações de Auditoria'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class WidgetAdminForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = '__all__'
        widgets = {
            'template_code': forms.Textarea(attrs={'rows': 15, 'class': 'html-editor'}),
            'css_code': forms.Textarea(attrs={'rows': 10, 'class': 'css-editor'}),
            'js_code': forms.Textarea(attrs={'rows': 10, 'class': 'js-editor'}),
            'default_settings': JsonWidget(),
        }


class WidgetAdmin(admin.ModelAdmin):
    form = WidgetAdminForm
    list_display = ('name', 'slug', 'widget_type', 'category', 'is_active')
    list_filter = ('widget_type', 'category', 'is_active')
    search_fields = ('name', 'slug', 'description', 'template_code')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('name', 'slug', 'description', 'widget_type', 'category', 'icon', 'is_active')
        }),
        (_('Código do Widget'), {
            'fields': ('template_code', 'css_code', 'js_code', 'default_settings')
        }),
        (_('Informações de Auditoria'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class WidgetInstanceAdminForm(forms.ModelForm):
    class Meta:
        model = WidgetInstance
        fields = '__all__'
        widgets = {
            'settings': JsonWidget(),
            'visibility_rules': JsonWidget(),
            'custom_css': forms.Textarea(attrs={'rows': 5, 'class': 'css-editor'}),
        }


class WidgetInstanceAdmin(admin.ModelAdmin):
    form = WidgetInstanceAdminForm
    list_display = ('widget', 'area', 'title', 'order', 'is_visible')
    list_filter = ('area__template', 'widget__widget_type', 'is_visible')
    search_fields = ('widget__name', 'area__name', 'title', 'custom_classes')
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('widget', 'area', 'title', 'order', 'is_visible')
        }),
        (_('Personalização'), {
            'fields': ('settings', 'custom_css', 'custom_classes')
        }),
        (_('Visibilidade Condicional'), {
            'fields': ('visibility_rules',)
        }),
        (_('Informações de Auditoria'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# Registra os modelos no admin
admin.site.register(TemplateCategory, TemplateCategoryAdmin)
admin.site.register(TemplateType, TemplateTypeAdmin)
admin.site.register(DjangoTemplate, DjangoTemplateAdmin)
admin.site.register(LayoutTemplate, LayoutTemplateAdmin)
admin.site.register(ComponentTemplate, ComponentTemplateAdmin)
admin.site.register(ComponentInstance, ComponentInstanceAdmin)
admin.site.register(Widget, WidgetAdmin)
admin.site.register(WidgetInstance, WidgetInstanceAdmin)