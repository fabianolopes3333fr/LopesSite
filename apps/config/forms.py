# apps/config/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import URLValidator
from .models import Page, SiteStyle, Menu, CustomField, FieldGroup
from colorfield.fields import ColorField
from django_ckeditor_5.widgets import CKEditor5Widget
from utils.constants import PAGE_STATUS, PAGE_TEMPLATES


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ['title', 'content', 'parent', 'status', 'meta_title', 'meta_description', 'meta_keywords', 'og_title', 'og_description', 'og_image', 'schema_type', 'schema_name', 'schema_description']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'ckeditor'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'meta_title': _('70 caractères maximum'),
            'meta_description': _('160 caractères maximum'),
            'meta_keywords': _('Séparez les mots-clés par des virgules'),
            'css_class': _('Classes CSS supplémentaires pour cette page'),
            'js_code': _('Code JavaScript spécifique à cette page')
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona classes Bootstrap
        for field in self.fields.values():
            if not isinstance(field.widget, (CKEditor5Widget, forms.CheckboxInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

    def clean_meta_title(self):
        meta_title = self.cleaned_data.get('meta_title')
        if meta_title and len(meta_title) > 70:  # Adicionado verificação
            raise forms.ValidationError(_('Le titre SEO ne doit pas dépasser 70 caractères.'))
        return meta_title

    def clean_meta_description(self):
        meta_description = self.cleaned_data.get('meta_description')
        if meta_description and len(meta_description) > 160:  # Adicionado verificação
            raise forms.ValidationError(_('La description SEO ne doit pas dépasser 160 caractères.'))
        return meta_description

    def clean_js_code(self):
        js_code = self.cleaned_data.get('js_code')
        if js_code:
            # Validação básica de JavaScript
            if 'document.write' in js_code:
                raise forms.ValidationError(_('L\'utilisation de document.write n\'est pas autorisée.'))
        return js_code
    
class CustomFieldForm(forms.ModelForm):
    value = forms.CharField(required=False)
    class Meta:
        model = CustomField
        fields = ['name', 'field_type', 'required', 'choices', 'group', 'order']
        widgets = {
            'field_type': forms.Select(attrs={'class': 'form-control'}),
        }

class FieldGroupForm(forms.ModelForm):
    class Meta:
        model = FieldGroup
        fields = ['name']

class SiteStyleForm(forms.ModelForm):
    class Meta:
        model = SiteStyle
        fields = [
            'primary_color', 
            'secondary_color', 
            'accent_color',
            'text_color',
            'link_color',
            'heading_color',
            'font_family', 
            'heading_font', 
            'base_font_size',
            'body_line_height',
            'heading_line_height',
            'container_width',
            'grid_gutter',
            'mobile_breakpoint',
            'tablet_breakpoint',
            'custom_css'
        ]
        widgets = {
            'custom_css': forms.Textarea(
                attrs={
                    'rows': 10, 
                    'class': 'form-control code-editor',
                    'spellcheck': 'false'
                }
            )
        }
        help_texts = {
            'custom_css': _('CSS personnalisé pour le site'),
            'font_family': _('Police principale (ex: Arial, sans-serif)'),
            'base_font_size': _('Taille en px, rem ou em (ex: 16px)'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field, ColorField):
                field.widget.attrs.update({'class': 'form-control'})

    def clean_custom_css(self):
        from utils.validators import validate_css
        css = self.cleaned_data.get('custom_css')
        if css:
            validate_css(css)
        return css

class MenuForm(forms.ModelForm):
    # Definir o campo page explicitamente
    page = forms.ModelChoiceField(
        queryset=Page.objects.filter(status='published'),
        required=False,
        label=_('Page'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Menu
        fields = [
            'name', 
            'url', 
            'page', 
            'parent', 
            'order', 
            'active',
            'icon',
            'target',
            'css_class',
            'description'
        ]
        widgets = {
            'description': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control'}
            ),
            'url': forms.URLInput(attrs={'class': 'form-control'})
        }
        help_texts = {
            'icon': _('Classe d\'icône FontAwesome (ex: fas fa-home)'),
            'css_class': _('Classes CSS supplémentaires pour ce menu'),
            'description': _('Description pour les menus déroulants')
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        url = cleaned_data.get('url')
        page = cleaned_data.get('page')

        if url and page:
            raise forms.ValidationError(
                _("Vous ne pouvez pas spécifier à la fois une URL et une page.")
            )
        elif not url and not page:
            raise forms.ValidationError(
                _("Vous devez spécifier soit une URL, soit une page.")
            )

        if url:
            try:
                URLValidator()(url)
            except forms.ValidationError:
                self.add_error('url', _("URL invalide"))

        return cleaned_data