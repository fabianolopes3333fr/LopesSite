from django import forms
from .models import Contact
from django.utils.translation import gettext_lazy as _

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Votre nom')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Votre email')}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Votre téléphone')}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Sujet')}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': _('Votre message')}),
        }