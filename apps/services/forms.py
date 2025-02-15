from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Service

class ProjectFilterForm(forms.Form):
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        empty_label=_("Tous les services"),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label=_("Date de début")
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label=_("Date de fin")
    )
    
    
class ServiceFilterForm(forms.Form):
    CATEGORY_CHOICES = [
        ('', _('Toutes les catégories')),
        ('residential', _('Résidentiel')),
        ('commercial', _('Commercial')),
        ('industrial', _('Industriel')),
        ('exterior', _('Extérieur')),
        ('interior', _('Intérieur')),
    ]

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Rechercher un service')})
    )

