from django import forms
from django.utils.translation import gettext_lazy as _

class ColorFilterForm(forms.Form):
    CHOICES = [
        ('all', _('Toutes les couleurs')),
        ('warm', _('Couleurs chaudes')),
        ('cool', _('Couleurs froides')),
        ('neutral', _('Couleurs neutres')),
    ]

    color_type = forms.ChoiceField(
        choices=CHOICES,
        required=False,
        label=_('Type de couleur'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        label=_('Rechercher'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom ou code de la couleur')})
    )
