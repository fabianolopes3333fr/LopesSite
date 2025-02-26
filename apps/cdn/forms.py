from django import forms
from .models import CDNProvider, CDNFile

class CDNProviderForm(forms.ModelForm):
    class Meta:
        model = CDNProvider
        fields = ['name', 'base_url', 'api_key', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'base_url': forms.URLInput(attrs={'class': 'form-control'}),
            'api_key': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_base_url(self):
        base_url = self.cleaned_data.get('base_url')
        if not base_url.startswith(('http://', 'https://')):
            raise forms.ValidationError("Base URL must start with 'http://' or 'https://'")
        return base_url

class CDNFileForm(forms.ModelForm):
    class Meta:
        model = CDNFile
        fields = ['file', 'provider', 'path', 'content_type']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'provider': forms.Select(attrs={'class': 'form-select'}),
            'path': forms.TextInput(attrs={'class': 'form-control'}),
            'content_type': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_path(self):
        path = self.cleaned_data.get('path')
        if path.startswith('/'):
            raise forms.ValidationError("Path should not start with a '/'")
        return path

    def clean_content_type(self):
        content_type = self.cleaned_data.get('content_type')
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'text/css', 'application/javascript']
        if content_type not in allowed_types:
            raise forms.ValidationError(f"Content type '{content_type}' is not allowed. Allowed types are: {', '.join(allowed_types)}")
        return content_type