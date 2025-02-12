from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Quote

class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['name', 'email', 'phone', 'service', 'area', 'details']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-control'}),
            'area': forms.NumberInput(attrs={'class': 'form-control'}),
            'details': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = _("Nom")
        self.fields['email'].label = _("Email")
        self.fields['phone'].label = _("Téléphone")
        self.fields['service'].label = _("Service demandé")
        self.fields['area'].label = _("Surface (m²)")
        self.fields['details'].label = _("Détails supplémentaires")